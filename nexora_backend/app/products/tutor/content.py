"""Source-aware curriculum access for the Tutor learning loop.

The read path prefers reviewed database content and keeps the original
foundation fixtures as a safe fallback until an official bundle is imported.
No network scraping happens in a learner request.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.products.tutor.curriculum import (
    Lesson as FixtureLesson,
    get_lesson as get_fixture_lesson,
    get_subject_lesson as get_fixture_subject_lesson,
    list_lessons as list_fixture_lessons,
)
from app.products.tutor.models import CurriculumLesson, CurriculumSource, CurriculumVersion


@dataclass(frozen=True)
class ResolvedLesson:
    id: str
    subject_code: str
    title_ar: str
    title_en: str
    summary_ar: str
    summary_en: str
    content_ar: str
    content_en: str
    skill_codes: tuple[str, ...]
    curriculum_version: str
    source_id: str | None = None
    source_name_ar: str | None = None
    source_name_en: str | None = None
    source_url: str | None = None
    source_locator: str | None = None
    source_status: str | None = None


def _from_fixture(lesson: FixtureLesson) -> ResolvedLesson:
    return ResolvedLesson(
        id=lesson.id,
        subject_code=lesson.subject_code,
        title_ar=lesson.title_ar,
        title_en=lesson.title_en,
        summary_ar=lesson.summary_ar,
        summary_en=lesson.summary_en,
        content_ar=lesson.summary_ar,
        content_en=lesson.summary_en,
        skill_codes=lesson.skill_codes,
        curriculum_version=lesson.curriculum_version,
        source_status="foundation_fixture",
    )


def _from_db(lesson: CurriculumLesson) -> ResolvedLesson:
    source = lesson.version.source if lesson.version and lesson.version.source else None
    return ResolvedLesson(
        id=lesson.id,
        subject_code=lesson.subject_code,
        title_ar=lesson.title_ar,
        title_en=lesson.title_en,
        summary_ar=lesson.summary_ar,
        summary_en=lesson.summary_en,
        content_ar=lesson.content_ar,
        content_en=lesson.content_en,
        skill_codes=tuple(lesson.skill_codes or []),
        curriculum_version=lesson.curriculum_version,
        source_id=source.id if source else None,
        source_name_ar=source.name_ar if source else None,
        source_name_en=source.name_en if source else None,
        source_url=lesson.source_url,
        source_locator=lesson.source_locator,
        source_status=source.license_status if source else "reviewed_official_content",
    )


def _published_query(db: Session, curriculum_version: str | None = None):
    query = (
        db.query(CurriculumLesson)
        .join(CurriculumVersion, CurriculumLesson.curriculum_version == CurriculumVersion.code)
        .join(CurriculumSource, CurriculumVersion.source_id == CurriculumSource.id)
        .options(joinedload(CurriculumLesson.version).joinedload(CurriculumVersion.source))
        .filter(
            CurriculumLesson.status == "published",
            CurriculumVersion.status == "published",
            CurriculumSource.is_active.is_(True),
            CurriculumSource.license_status == "approved",
        )
    )
    if curriculum_version:
        query = query.filter(CurriculumLesson.curriculum_version == curriculum_version)
    return query


def list_lessons(
    db: Session,
    subject_code: str | None = None,
    curriculum_version: str | None = None,
) -> list[dict]:
    query = _published_query(db, curriculum_version)
    if subject_code:
        query = query.filter(CurriculumLesson.subject_code == subject_code)
    lessons = query.order_by(CurriculumLesson.id).all()
    if lessons:
        return [lesson_summary(_from_db(lesson)) for lesson in lessons]

    fixtures = list_fixture_lessons(subject_code)
    if curriculum_version and curriculum_version != "egypt-secondary-2026":
        return []
    return [lesson_summary(_from_fixture(_fixture_from_dict(item))) for item in fixtures]


def get_lesson(
    db: Session,
    lesson_id: str | None,
    curriculum_version: str | None = None,
) -> ResolvedLesson | None:
    if not lesson_id:
        return None
    query = _published_query(db, curriculum_version).filter(CurriculumLesson.id == lesson_id)
    lesson = query.first()
    if lesson:
        return _from_db(lesson)
    fixture = get_fixture_lesson(lesson_id)
    if fixture and (not curriculum_version or fixture.curriculum_version == curriculum_version):
        return _from_fixture(fixture)
    return None


def get_subject_lesson(
    db: Session,
    subject_code: str,
    curriculum_version: str | None = None,
) -> ResolvedLesson | None:
    query = _published_query(db, curriculum_version).filter(
        CurriculumLesson.subject_code == subject_code
    )
    lesson = query.order_by(CurriculumLesson.id).first()
    if lesson:
        return _from_db(lesson)
    fixture = get_fixture_subject_lesson(subject_code)
    if fixture and (not curriculum_version or fixture.curriculum_version == curriculum_version):
        return _from_fixture(fixture)
    return None


def lesson_summary(lesson: ResolvedLesson) -> dict:
    return {
        "id": lesson.id,
        "subject_code": lesson.subject_code,
        "title_ar": lesson.title_ar,
        "title_en": lesson.title_en,
        "summary_ar": lesson.summary_ar,
        "summary_en": lesson.summary_en,
        "skill_codes": list(lesson.skill_codes),
        "curriculum_version": lesson.curriculum_version,
        "source_id": lesson.source_id,
        "source_name_ar": lesson.source_name_ar,
        "source_name_en": lesson.source_name_en,
        "source_url": lesson.source_url,
        "source_locator": lesson.source_locator,
        "source_status": lesson.source_status,
    }


def _fixture_from_dict(item: dict) -> FixtureLesson:
    return FixtureLesson(
        id=item["id"],
        subject_code=item["subject_code"],
        title_ar=item["title_ar"],
        title_en=item["title_en"],
        summary_ar=item["summary_ar"],
        summary_en=item["summary_en"],
        skill_codes=tuple(item["skill_codes"]),
        curriculum_version=item["curriculum_version"],
    )
