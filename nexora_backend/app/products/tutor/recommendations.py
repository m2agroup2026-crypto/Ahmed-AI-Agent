"""Deterministic next-step recommendations from real learner activity."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.products.tutor.models import (
    AssessmentAttempt,
    CurriculumLesson,
    CurriculumQuestion,
    LearnerProfile,
)
from app.products.tutor.practice import _published_question_query, _question_view
from app.products.tutor.progress import get_progress

REASON_MESSAGES = {
    "start_learning": (
        "ابدأ بأول تدريب موثّق في منهجك الحالي.",
        "Start with your first source-grounded practice question.",
    ),
    "practice_focus_skill": (
        "هذا التدريب يركّز على المهارة التي تحتاج دعمًا أكبر.",
        "This practice focuses on the skill that needs the most support.",
    ),
    "review_focus_skill": (
        "سنراجع هذه المهارة مرة أخرى لتثبيت الفهم.",
        "We will review this skill again to strengthen understanding.",
    ),
    "continue_curriculum": (
        "هذه هي الخطوة التالية المتاحة في منهجك المنشور.",
        "This is the next available step in your published curriculum.",
    ),
}


def get_recommendation(
    db: Session,
    user_id: int,
    subject_code: str | None = None,
    curriculum_version: str = "egypt-secondary-2026",
) -> dict:
    """Return one safe, explainable practice recommendation.

    Recommendations use only published questions from active, rights-approved
    curriculum and only the authenticated learner's own attempts. Foundation
    fixtures are intentionally not eligible for this path.
    """

    selected_subject = _resolve_subject(db, user_id, subject_code, curriculum_version)
    progress = get_progress(db, user_id, curriculum_version, selected_subject)
    skill_accuracy = {
        item["skill_code"]: item["accuracy_percent"]
        for item in progress["skills"]
    }
    focus_skill = progress["next_focus_skill"]

    query = _published_question_query(db).filter(
        CurriculumLesson.subject_code == selected_subject,
        CurriculumLesson.curriculum_version == curriculum_version,
    )
    attempted_question_ids = select(AssessmentAttempt.question_id).where(
        AssessmentAttempt.user_id == user_id
    )

    def pick(skill_code: str | None = None, *, unattempted: bool) -> CurriculumQuestion | None:
        candidate_query = query
        if skill_code:
            candidate_query = candidate_query.filter(
                CurriculumQuestion.skill_code == skill_code
            )
        if unattempted:
            candidate_query = candidate_query.filter(
                ~CurriculumQuestion.id.in_(attempted_question_ids)
            )
        return candidate_query.order_by(CurriculumQuestion.id).first()

    reason_code = "continue_curriculum"
    question: CurriculumQuestion | None = None
    if progress["attempts"] == 0:
        question = pick(unattempted=True)
        reason_code = "start_learning"
    elif focus_skill:
        question = pick(focus_skill, unattempted=True)
        if question:
            reason_code = "practice_focus_skill"
        else:
            question = pick(focus_skill, unattempted=False)
            if question:
                reason_code = "review_focus_skill"

    if question is None:
        question = pick(unattempted=True)
        reason_code = "continue_curriculum"

    if question is None and focus_skill:
        question = pick(focus_skill, unattempted=False)
        reason_code = "review_focus_skill"

    if question is None:
        raise HTTPException(status_code=404, detail="No published practice question is available")

    message_ar, message_en = REASON_MESSAGES[reason_code]
    return {
        "status": "available",
        "reason_code": reason_code,
        "message_ar": message_ar,
        "message_en": message_en,
        "subject_code": selected_subject,
        "curriculum_version": curriculum_version,
        "skill_code": question.skill_code or focus_skill,
        "skill_accuracy_percent": skill_accuracy.get(question.skill_code or focus_skill),
        "question": _question_view(question),
    }


def _resolve_subject(
    db: Session,
    user_id: int,
    subject_code: str | None,
    curriculum_version: str,
) -> str:
    if subject_code:
        return subject_code

    available_subjects = [
        row[0]
        for row in (
            _published_question_query(db)
            .filter(CurriculumLesson.curriculum_version == curriculum_version)
            .with_entities(CurriculumLesson.subject_code)
            .distinct()
            .order_by(CurriculumLesson.subject_code)
            .all()
        )
    ]
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    configured_subjects = list(profile.subject_codes or []) if profile else []
    for configured_subject in configured_subjects:
        if configured_subject in available_subjects:
            return configured_subject
    if available_subjects:
        return available_subjects[0]
    raise HTTPException(status_code=404, detail="No published practice question is available")
