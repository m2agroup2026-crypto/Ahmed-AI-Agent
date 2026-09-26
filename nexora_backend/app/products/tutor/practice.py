"""Deterministic, source-grounded practice and assessment services."""

from dataclasses import dataclass
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.products.tutor.models import (
    AssessmentAttempt,
    CurriculumLesson,
    CurriculumQuestion,
    CurriculumSource,
    CurriculumVersion,
    LearningSession,
)


@dataclass(frozen=True)
class PracticeResult:
    attempt_id: str
    question_id: str
    is_correct: bool
    score: int
    max_score: int
    explanation_ar: str
    explanation_en: str
    source_url: str
    source_locator: str
    next_action: str


def _published_question_query(db: Session):
    return (
        db.query(CurriculumQuestion)
        .join(CurriculumLesson, CurriculumQuestion.lesson_id == CurriculumLesson.id)
        .join(CurriculumVersion, CurriculumLesson.curriculum_version == CurriculumVersion.code)
        .join(CurriculumSource, CurriculumVersion.source_id == CurriculumSource.id)
        .options(
            joinedload(CurriculumQuestion.lesson).joinedload(
                CurriculumLesson.version
            ).joinedload(CurriculumVersion.source)
        )
        .filter(
            CurriculumQuestion.status == "published",
            CurriculumLesson.status == "published",
            CurriculumVersion.status == "published",
            CurriculumSource.is_active.is_(True),
            CurriculumSource.license_status == "approved",
        )
    )


def _question_view(question: CurriculumQuestion) -> dict:
    lesson = question.lesson
    source = lesson.version.source
    return {
        "id": question.id,
        "lesson_id": question.lesson_id,
        "subject_code": lesson.subject_code,
        "skill_code": question.skill_code,
        "question_type": question.question_type,
        "prompt_ar": question.prompt_ar,
        "prompt_en": question.prompt_en,
        "choices_ar": list(question.choices_ar or []),
        "choices_en": list(question.choices_en or []),
        "curriculum_version": lesson.curriculum_version,
        "source_url": lesson.source_url,
        "source_locator": question.source_locator,
        "source_status": source.license_status,
    }


def get_next_question(
    db: Session,
    user_id: int,
    subject_code: str,
    curriculum_version: str,
    lesson_id: str | None = None,
    skill_code: str | None = None,
) -> dict:
    query = _published_question_query(db).filter(
        CurriculumLesson.subject_code == subject_code,
        CurriculumLesson.curriculum_version == curriculum_version,
    )
    if lesson_id:
        query = query.filter(CurriculumQuestion.lesson_id == lesson_id)
    if skill_code:
        query = query.filter(CurriculumQuestion.skill_code == skill_code)

    attempted_ids = {
        row[0]
        for row in db.query(AssessmentAttempt.question_id)
        .filter(AssessmentAttempt.user_id == user_id)
        .all()
    }
    unattempted_query = query.order_by(CurriculumQuestion.id)
    if attempted_ids:
        unattempted_query = unattempted_query.filter(
            ~CurriculumQuestion.id.in_(attempted_ids)
        )
    question = unattempted_query.first() or query.order_by(CurriculumQuestion.id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="No published practice question is available")
    return _question_view(question)


def _normalize_answer(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return " ".join(normalized.split())


def submit_attempt(
    db: Session,
    user_id: int,
    question_id: str,
    submitted_answer: str,
    locale: str,
    session_id: str | None = None,
) -> PracticeResult:
    question = _published_question_query(db).filter(CurriculumQuestion.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Published practice question not found")

    if session_id:
        learning_session = (
            db.query(LearningSession)
            .filter(LearningSession.id == session_id, LearningSession.user_id == user_id)
            .first()
        )
        if learning_session is None:
            raise HTTPException(status_code=404, detail="Learning session not found")
        if (
            learning_session.subject_code != question.lesson.subject_code
            or learning_session.curriculum_version != question.lesson.curriculum_version
        ):
            raise HTTPException(status_code=422, detail="Question does not belong to this session")

    submitted = _normalize_answer(submitted_answer)
    accepted = {_normalize_answer(answer) for answer in question.accepted_answers}
    is_correct = submitted in accepted
    score = question.points if is_correct else 0
    attempt = AssessmentAttempt(
        user_id=user_id,
        question_id=question.id,
        session_id=session_id,
        submitted_answer=submitted_answer,
        is_correct=is_correct,
        score=score,
        locale=locale,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return PracticeResult(
        attempt_id=attempt.id,
        question_id=question.id,
        is_correct=is_correct,
        score=score,
        max_score=question.points,
        explanation_ar=question.explanation_ar,
        explanation_en=question.explanation_en,
        source_url=question.lesson.source_url,
        source_locator=question.source_locator,
        next_action="continue" if is_correct else "review",
    )
