from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.products.tutor.content import ResolvedLesson, get_lesson, get_subject_lesson
from app.products.tutor.models import LearnerProfile, LearningMessage, LearningSession
from app.products.tutor.schemas import SUPPORTED_SUBJECTS, TutorProfileUpdate


def require_active_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active user required")
    return user


def get_profile(db: Session, user_id: int) -> LearnerProfile:
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor profile not found")
    return profile


def save_profile(db: Session, user_id: int, payload: TutorProfileUpdate) -> LearnerProfile:
    invalid_subjects = set(payload.subject_codes) - SUPPORTED_SUBJECTS
    if invalid_subjects:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported subjects: {', '.join(sorted(invalid_subjects))}",
        )

    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if profile is None:
        profile = LearnerProfile(user_id=user_id, grade_level=payload.grade_level)
        db.add(profile)

    profile.grade_level = payload.grade_level
    profile.locale = payload.locale
    profile.subject_codes = payload.subject_codes
    profile.learning_preferences = payload.learning_preferences
    db.commit()
    db.refresh(profile)
    return profile


def create_session(db: Session, user_id: int, subject_code: str, curriculum_version: str) -> LearningSession:
    if subject_code not in SUPPORTED_SUBJECTS:
        raise HTTPException(status_code=422, detail="Unsupported subject")
    session = LearningSession(
        user_id=user_id,
        subject_code=subject_code,
        curriculum_version=curriculum_version,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, user_id: int, session_id: str) -> LearningSession:
    session = (
        db.query(LearningSession)
        .filter(LearningSession.id == session_id, LearningSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning session not found")
    return session


@dataclass(frozen=True)
class CurriculumAnswer:
    status: str
    content: str
    lesson: ResolvedLesson | None = None
    adaptation_mode: str = "standard"
    next_action: str | None = None


def answer_from_curriculum(
    db: Session,
    subject_code: str,
    curriculum_version: str,
    lesson_id: str | None,
    locale: str,
    profile: LearnerProfile | None = None,
) -> CurriculumAnswer:
    lesson = get_lesson(db, lesson_id, curriculum_version) or get_subject_lesson(
        db, subject_code, curriculum_version
    )
    if lesson is None:
        return CurriculumAnswer(
            status="needs_context",
            content=(
                "اختر درسًا من المنهج لأشرح لك محتواه."
                if locale.startswith("ar")
                else "Choose a curriculum lesson so I can explain it."
            ),
        )

    preferences = (profile.learning_preferences if profile else {}) or {}
    detail_level = preferences.get("detail_level", "standard")
    if detail_level == "concise":
        content = lesson.summary_ar if locale.startswith("ar") else lesson.summary_en
        adaptation_mode = "concise"
    else:
        content = lesson.content_ar if locale.startswith("ar") else lesson.content_en
        adaptation_mode = "standard"

    next_action = "practice" if preferences.get("next_step", "practice") == "practice" else "continue"
    return CurriculumAnswer(
        status="curriculum_context",
        content=content,
        lesson=lesson,
        adaptation_mode=adaptation_mode,
        next_action=next_action,
    )


def append_message(
    db: Session,
    session: LearningSession,
    content: str,
    lesson_id: str | None,
    locale: str,
) -> tuple[
    LearningMessage,
    LearningMessage | None,
    str,
    str | None,
    str | None,
    str,
    str | None,
    str | None,
    str,
    str | None,
]:
    learner_message = LearningMessage(
        session_id=session.id,
        role="learner",
        content=content,
        lesson_id=lesson_id,
    )
    db.add(learner_message)
    db.flush()

    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == session.user_id).first()
    answer = answer_from_curriculum(
        db,
        session.subject_code,
        session.curriculum_version,
        lesson_id,
        locale,
        profile,
    )
    tutor_message = None
    source_lesson_id = None
    source_title = None
    if answer.lesson:
        source_lesson_id = answer.lesson.id
        source_title = (
            answer.lesson.title_ar if locale.startswith("ar") else answer.lesson.title_en
        )
        tutor_message = LearningMessage(
            session_id=session.id,
            role="tutor",
            content=answer.content,
            lesson_id=source_lesson_id,
        )
        db.add(tutor_message)

    db.commit()
    db.refresh(learner_message)
    if tutor_message:
        db.refresh(tutor_message)
    return (
        learner_message,
        tutor_message,
        answer.status,
        source_lesson_id,
        source_title,
        answer.content,
        answer.lesson.source_url if answer.lesson else None,
        answer.lesson.source_locator if answer.lesson else None,
        answer.adaptation_mode,
        answer.next_action,
    )
