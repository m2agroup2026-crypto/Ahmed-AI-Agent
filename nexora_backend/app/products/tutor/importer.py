"""Idempotent, policy-aware curriculum bundle imports.

The importer is deliberately boring: it stores the source and the exact
content bundle, updates existing records by their stable identifiers, and
never makes unlicensed content learner-visible.  A later ingestion worker can
build the same payload from an approved Ministry source without changing the
learner API.
"""

from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.products.tutor.models import (
    CurriculumQuestion,
    CurriculumLesson,
    CurriculumSkill,
    CurriculumSource,
    CurriculumVersion,
    CurriculumUnit,
)
from app.products.tutor.schemas import CurriculumImportPayload, CurriculumImportResult, CurriculumQuestionInput


APPROVED_LICENSE_STATUS = "approved"


def _now() -> datetime:
    return datetime.now(UTC)


def _merge_import_payload(db: Session, payload: CurriculumImportPayload) -> CurriculumImportPayload:
    """Build detached final values; omitted fields retain their stored values."""
    def merge(item, model, key):
        existing = db.get(model, key)
        values = item.model_dump()
        if existing is not None:
            for field in type(item).model_fields:
                if field not in item.model_fields_set and hasattr(existing, field):
                    values[field] = getattr(existing, field)
        return values

    values = payload.model_dump()
    values["source"] = merge(payload.source, CurriculumSource, payload.source.id)
    values["version"] = merge(payload.version, CurriculumVersion, payload.version.code)
    for field, model, key in [("units", CurriculumUnit, "id"),
                              ("skills", CurriculumSkill, "code"),
                              ("lessons", CurriculumLesson, "id"),
                              ("questions", CurriculumQuestion, "id")]:
        values[field] = [merge(item, model, getattr(item, key)) for item in getattr(payload, field)]
    try:
        return CurriculumImportPayload.model_validate(values)
    except ValidationError as error:
        raise HTTPException(422, detail=f"Merged curriculum content is incompatible: {error}") from error


def _validate_content_languages(db: Session, payload: CurriculumImportPayload) -> None:
    """Validate declared source fields before any upsert; never infer language."""
    def declared(item, existing):
        if "content_language" in item.model_fields_set:
            return item.content_language
        return existing.content_language if existing else None

    def require_text(item, language, fields, label):
        if language not in {"ar", "en"}:
            raise HTTPException(422, detail=f"{label}: content_language must be declared as ar or en")
        missing = [f"{field}_{language}" for field in fields
                   if not getattr(item, f"{field}_{language}").strip()]
        if missing:
            raise HTTPException(422, detail=f"{label}: missing source-language fields: {', '.join(missing)}")

    version = db.get(CurriculumVersion, payload.version.code)
    version_language = declared(payload.version, version)
    if not (payload.source.name_ar.strip() or payload.source.name_en.strip()):
        raise HTTPException(422, detail="Source requires its original name")
    if version_language:
        require_text(payload.version, version_language, ("title",), "Version")
    elif not (payload.version.title_ar.strip() or payload.version.title_en.strip()):
        raise HTTPException(422, detail="Version requires its original title")

    units = {unit.id: unit for unit in db.query(CurriculumUnit).filter(
        CurriculumUnit.curriculum_version == payload.version.code).all()}
    units.update({unit.id: unit for unit in payload.units})
    for unit in units.values():
        language = unit.content_language or version_language
        require_text(unit, language, ("title",), f"Unit {unit.id}")

    lesson_languages = {}
    skill_languages = {}
    lessons = {lesson.id: lesson for lesson in db.query(CurriculumLesson).filter(
        CurriculumLesson.curriculum_version == payload.version.code).all()}
    lessons.update({lesson.id: lesson for lesson in payload.lessons})
    for lesson in lessons.values():
        language = lesson.content_language or version_language
        require_text(lesson, language, ("title", "summary", "content"), f"Lesson {lesson.id}")
        lesson_languages[lesson.id] = language
        for code in lesson.skill_codes:
            skill_languages.setdefault(code, set()).add(language)
    questions = {question.id: question for question in db.query(CurriculumQuestion).filter(
        CurriculumQuestion.lesson_id.in_(list(lessons))).all()}
    questions.update({question.id: question for question in payload.questions})
    for question in questions.values():
        try:
            CurriculumQuestionInput.model_validate({
                field: getattr(question, field) for field in CurriculumQuestionInput.model_fields
                if hasattr(question, field)
            })
        except ValidationError as error:
            raise HTTPException(422, detail=f"Question {question.id}: incompatible merged choices: {error}") from error
        language = lesson_languages.get(question.lesson_id)
        if language is None:
            lesson = db.get(CurriculumLesson, question.lesson_id)
            if lesson is None or lesson.curriculum_version != payload.version.code:
                raise HTTPException(422, detail=f"Question references an unknown lesson: {question.lesson_id}")
            language = lesson.content_language or version_language
        if getattr(question, "content_language", None) is not None and question.content_language != language:
            raise HTTPException(422, detail=f"Question {question.id}: content_language must match its lesson")
        require_text(question, language, ("prompt", "explanation"), f"Question {question.id}")
        if question.question_type == "single_choice":
            choices = getattr(question, f"choices_{language}")
            if not choices or any(not (choice if isinstance(choice, str) else
                                      choice["label"] if isinstance(choice, dict) else choice.label).strip()
                                  for choice in choices):
                raise HTTPException(422, detail=f"Question {question.id}: choices_{language} requires source choices")
        if question.skill_code:
            skill_languages.setdefault(question.skill_code, set()).add(language)
    skills = {skill.code: skill for skill in db.query(CurriculumSkill).filter(
        CurriculumSkill.curriculum_version == payload.version.code).all()}
    skills.update({skill.code: skill for skill in payload.skills})
    for skill in skills.values():
        # Skills use the declared languages of their lesson/question references.
        # An unreferenced skill requires an explicit version default instead.
        for language in skill_languages.get(skill.code, {version_language}):
            require_text(skill, language, ("title", "description"), f"Skill {skill.code}")


def import_curriculum_bundle(
    db: Session, payload: CurriculumImportPayload
) -> CurriculumImportResult:
    """Restore the request session after a database failure and propagate it."""
    try:
        return _import_curriculum_bundle(db, payload)
    except SQLAlchemyError:
        db.rollback()
        raise


def _import_curriculum_bundle(
    db: Session, payload: CurriculumImportPayload
) -> CurriculumImportResult:
    """Upsert a reviewed curriculum bundle and return import counts.

    ``published`` lessons are accepted only from an active source whose rights
    have been explicitly approved.  This is a hard safety boundary: draft and
    review content may be imported for editorial work, but it is not returned
    by the learner read path.
    """

    # All language/linkage checks run against detached merged values, before
    # modifying ORM records or flushing anything from this import.
    with db.no_autoflush:
        payload = _merge_import_payload(db, payload)
        _validate_content_languages(db, payload)
    source_input = payload.source
    version_input = payload.version
    # Validate the additive unit linkage before mutating any existing records.
    unit_inputs = {unit.id: unit for unit in payload.units}
    if len(unit_inputs) != len(payload.units):
        raise HTTPException(status_code=422, detail="Duplicate curriculum unit identifier")
    for unit_input in payload.units:
        existing = db.get(CurriculumUnit, unit_input.id)
        if existing and (
            existing.curriculum_version != version_input.code
            or existing.subject_code != unit_input.subject_code
        ):
            raise HTTPException(status_code=422, detail="Unit belongs to another curriculum or subject")
    for lesson_input in payload.lessons:
        existing_lesson = db.get(CurriculumLesson, lesson_input.id)
        # Old bundles omit unit_id and retain any previously imported linkage.
        unit_id = lesson_input.unit_id
        if "unit_id" not in lesson_input.model_fields_set and existing_lesson:
            unit_id = existing_lesson.unit_id
        if unit_id:
            unit = unit_inputs.get(unit_id) or db.get(CurriculumUnit, unit_id)
            if unit is None or unit.subject_code != lesson_input.subject_code or (
                unit_id not in unit_inputs and unit.curriculum_version != version_input.code
            ):
                raise HTTPException(status_code=422, detail="Lesson unit must match its curriculum and subject")
    has_published_lesson = any(lesson.status == "published" for lesson in payload.lessons)
    if (
        version_input.status == "published" or has_published_lesson
    ) and (
        source_input.license_status != APPROVED_LICENSE_STATUS or not source_input.is_active
    ):
        raise HTTPException(
            status_code=422,
            detail="Published curriculum content requires an active source with approved rights.",
        )
    if has_published_lesson and version_input.status != "published":
        raise HTTPException(
            status_code=422,
            detail="A published lesson requires a published curriculum version.",
        )

    lesson_inputs = {lesson.id: lesson for lesson in payload.lessons}
    published_questions = 0
    for question_input in payload.questions:
        if question_input.status == "published":
            lesson = lesson_inputs.get(question_input.lesson_id)
            if (version_input.status != "published"
                    or source_input.license_status != APPROVED_LICENSE_STATUS
                    or not source_input.is_active or lesson is None or lesson.status != "published"):
                raise HTTPException(
                    status_code=422,
                    detail="A published question requires a published lesson, version, and approved source rights.",
                )
            published_questions += 1

    source = db.get(CurriculumSource, source_input.id)
    if source is None:
        source = CurriculumSource(id=source_input.id)
        db.add(source)

    source.name_ar = source_input.name_ar
    source.name_en = source_input.name_en
    source.source_type = source_input.source_type
    source.base_url = source_input.base_url
    source.license_status = source_input.license_status
    source.is_active = source_input.is_active

    version = db.get(CurriculumVersion, version_input.code)
    if version is None:
        version = CurriculumVersion(code=version_input.code)
        db.add(version)

    version.source_id = source.id
    version.title_ar = version_input.title_ar
    version.title_en = version_input.title_en
    version.stage = version_input.stage
    version.grade_level = version_input.grade_level
    version.academic_year = version_input.academic_year
    if "content_language" in version_input.model_fields_set:
        version.content_language = version_input.content_language
    version.status = version_input.status

    db.flush()
    for unit_input in payload.units:
        unit = db.get(CurriculumUnit, unit_input.id)
        if unit is None:
            unit = CurriculumUnit(id=unit_input.id)
            db.add(unit)
        unit.curriculum_version = version.code
        unit.subject_code = unit_input.subject_code
        if "content_language" in unit_input.model_fields_set:
            unit.content_language = unit_input.content_language
        unit.title_ar = unit_input.title_ar
        unit.title_en = unit_input.title_en
        unit.position = unit_input.position
    # Session factories also use autoflush=False; persist parents first.
    db.flush()

    for skill_input in payload.skills:
        skill = db.get(CurriculumSkill, skill_input.code)
        if skill is None:
            skill = CurriculumSkill(code=skill_input.code)
            db.add(skill)
        skill.curriculum_version = version.code
        skill.subject_code = skill_input.subject_code
        skill.title_ar = skill_input.title_ar
        skill.title_en = skill_input.title_en
        skill.description_ar = skill_input.description_ar
        skill.description_en = skill_input.description_en

    published_lessons = 0
    for lesson_input in payload.lessons:
        if lesson_input.status == "published":
            published_lessons += 1

        lesson = db.get(CurriculumLesson, lesson_input.id)
        if lesson is None:
            lesson = CurriculumLesson(id=lesson_input.id)
            db.add(lesson)

        lesson.curriculum_version = version.code
        lesson.subject_code = lesson_input.subject_code
        if "content_language" in lesson_input.model_fields_set:
            lesson.content_language = lesson_input.content_language
        if "unit_id" in lesson_input.model_fields_set:
            lesson.unit_id = lesson_input.unit_id
        if "position" in lesson_input.model_fields_set:
            lesson.position = lesson_input.position
        lesson.title_ar = lesson_input.title_ar
        lesson.title_en = lesson_input.title_en
        lesson.summary_ar = lesson_input.summary_ar
        lesson.summary_en = lesson_input.summary_en
        lesson.content_ar = lesson_input.content_ar
        lesson.content_en = lesson_input.content_en
        lesson.skill_codes = lesson_input.skill_codes
        lesson.source_url = lesson_input.source_url
        lesson.source_locator = lesson_input.source_locator
        lesson.source_checksum = lesson_input.source_checksum
        lesson.status = lesson_input.status

    db.flush()
    for question_input in payload.questions:
        question = db.get(CurriculumQuestion, question_input.id)
        if question is None:
            question = CurriculumQuestion(id=question_input.id)
            db.add(question)

        question.lesson_id = question_input.lesson_id
        question.skill_code = question_input.skill_code
        question.question_type = question_input.question_type
        question.prompt_ar = question_input.prompt_ar
        question.prompt_en = question_input.prompt_en
        question.choices_ar = question_input.model_dump()["choices_ar"]
        question.choices_en = question_input.model_dump()["choices_en"]
        question.accepted_answers = question_input.accepted_answers
        question.explanation_ar = question_input.explanation_ar
        question.explanation_en = question_input.explanation_en
        question.source_locator = question_input.source_locator
        question.source_checksum = question_input.source_checksum
        question.points = question_input.points
        question.status = question_input.status

    source.last_synced_at = _now()
    db.commit()
    return CurriculumImportResult(
        source_id=source.id,
        curriculum_version=version.code,
        imported_lessons=len(payload.lessons),
        imported_skills=len(payload.skills),
        published_lessons=published_lessons,
        imported_questions=len(payload.questions),
        published_questions=published_questions,
        imported_units=len(payload.units),
    )
