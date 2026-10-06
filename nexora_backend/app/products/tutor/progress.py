"""Derived learner progress from immutable assessment attempts."""

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.products.tutor.models import (
    AssessmentAttempt,
    CurriculumLesson,
    CurriculumQuestion,
    CurriculumSource,
    CurriculumVersion,
)


def get_progress(
    db: Session,
    user_id: int,
    curriculum_version: str | None = None,
    subject_code: str | None = None,
) -> dict:
    """Return only progress represented by the user's persisted attempts.

    The query is intentionally scoped to currently published, rights-approved
    content. Attempts against retired content remain in the audit table but do
    not silently affect the active learner view.
    """

    query = (
        db.query(AssessmentAttempt, CurriculumQuestion, CurriculumLesson)
        .join(CurriculumQuestion, AssessmentAttempt.question_id == CurriculumQuestion.id)
        .join(CurriculumLesson, CurriculumQuestion.lesson_id == CurriculumLesson.id)
        .join(CurriculumVersion, CurriculumLesson.curriculum_version == CurriculumVersion.code)
        .join(CurriculumSource, CurriculumVersion.source_id == CurriculumSource.id)
        .filter(
            AssessmentAttempt.user_id == user_id,
            CurriculumQuestion.status == "published",
            CurriculumLesson.status == "published",
            CurriculumVersion.status == "published",
            CurriculumSource.is_active.is_(True),
            CurriculumSource.license_status == "approved",
        )
    )
    if curriculum_version:
        query = query.filter(CurriculumLesson.curriculum_version == curriculum_version)
    if subject_code:
        query = query.filter(CurriculumLesson.subject_code == subject_code)

    rows = query.order_by(AssessmentAttempt.created_at.asc()).all()
    skills: dict[str, dict] = defaultdict(
        lambda: {"attempts": 0, "correct": 0, "score": 0, "max_score": 0}
    )
    correct_answers = 0
    score = 0
    max_score = 0
    last_activity_at: datetime | None = None
    curriculum_versions: set[str] = set()
    subjects: set[str] = set()

    for attempt, question, lesson in rows:
        correct_answers += int(attempt.is_correct)
        score += attempt.score
        max_score += question.points
        last_activity_at = attempt.created_at
        curriculum_versions.add(lesson.curriculum_version)
        subjects.add(lesson.subject_code)
        if question.skill_code:
            skill = skills[question.skill_code]
            skill["attempts"] += 1
            skill["correct"] += int(attempt.is_correct)
            skill["score"] += attempt.score
            skill["max_score"] += question.points

    skill_rows = []
    for code, values in sorted(skills.items()):
        skill_rows.append(
            {
                "skill_code": code,
                "attempts": values["attempts"],
                "correct_answers": values["correct"],
                "score": values["score"],
                "max_score": values["max_score"],
                "accuracy_percent": _percent(values["correct"], values["attempts"]),
            }
        )

    next_focus_skill = None
    if skill_rows:
        next_focus_skill = min(
            skill_rows,
            key=lambda item: (item["accuracy_percent"], -item["attempts"], item["skill_code"]),
        )["skill_code"]

    return {
        "curriculum_version": curriculum_version or _single_or_none(curriculum_versions),
        "subject_code": subject_code or _single_or_none(subjects),
        "attempts": len(rows),
        "correct_answers": correct_answers,
        "score": score,
        "max_score": max_score,
        "accuracy_percent": _percent(correct_answers, len(rows)),
        "skills": skill_rows,
        "next_focus_skill": next_focus_skill,
        "last_activity_at": last_activity_at,
    }


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _single_or_none(values: set[str]) -> str | None:
    return next(iter(values)) if len(values) == 1 else None
