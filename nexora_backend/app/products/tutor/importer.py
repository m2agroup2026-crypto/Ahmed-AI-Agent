"""Idempotent, policy-aware curriculum bundle imports.

The importer is deliberately boring: it stores the source and the exact
content bundle, updates existing records by their stable identifiers, and
never makes unlicensed content learner-visible.  A later ingestion worker can
build the same payload from an approved Ministry source without changing the
learner API.
"""

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.products.tutor.models import (
    CurriculumQuestion,
    CurriculumLesson,
    CurriculumSkill,
    CurriculumSource,
    CurriculumVersion,
)
from app.products.tutor.schemas import CurriculumImportPayload, CurriculumImportResult


APPROVED_LICENSE_STATUS = "approved"


def _now() -> datetime:
    return datetime.now(UTC)


def import_curriculum_bundle(
    db: Session, payload: CurriculumImportPayload
) -> CurriculumImportResult:
    """Upsert a reviewed curriculum bundle and return import counts.

    ``published`` lessons are accepted only from an active source whose rights
    have been explicitly approved.  This is a hard safety boundary: draft and
    review content may be imported for editorial work, but it is not returned
    by the learner read path.
    """

    source_input = payload.source
    version_input = payload.version
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
    version.status = version_input.status

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

    lesson_ids = {lesson.id for lesson in payload.lessons}
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

    published_questions = 0
    for question_input in payload.questions:
        if question_input.lesson_id not in lesson_ids:
            existing_lesson = db.get(CurriculumLesson, question_input.lesson_id)
            if existing_lesson is None or existing_lesson.curriculum_version != version.code:
                raise HTTPException(
                    status_code=422,
                    detail=f"Question references an unknown lesson: {question_input.lesson_id}",
                )

        if question_input.status == "published":
            if (
                version.status != "published"
                or source.license_status != APPROVED_LICENSE_STATUS
                or question_input.lesson_id not in lesson_ids
                or next(
                    lesson.status
                    for lesson in payload.lessons
                    if lesson.id == question_input.lesson_id
                )
                != "published"
            ):
                raise HTTPException(
                    status_code=422,
                    detail="A published question requires a published lesson, version, and approved source rights.",
                )
            published_questions += 1

        question = db.get(CurriculumQuestion, question_input.id)
        if question is None:
            question = CurriculumQuestion(id=question_input.id)
            db.add(question)

        question.lesson_id = question_input.lesson_id
        question.skill_code = question_input.skill_code
        question.question_type = question_input.question_type
        question.prompt_ar = question_input.prompt_ar
        question.prompt_en = question_input.prompt_en
        question.choices_ar = question_input.choices_ar
        question.choices_en = question_input.choices_en
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
    )
