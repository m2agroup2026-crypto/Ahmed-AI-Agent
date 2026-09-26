from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user_id
from app.database.dependencies import get_db
from app.products.tutor.curriculum import list_lessons
from app.products.tutor.schemas import (
    LessonSummary,
    MessageCreate,
    MessageExchange,
    MessageView,
    SessionCreate,
    SessionResponse,
    TutorAnswer,
    TutorProfileResponse,
    TutorProfileUpdate,
)
from app.products.tutor.services import (
    append_message,
    create_session,
    get_profile,
    get_session,
    require_active_user,
    save_profile,
)


router = APIRouter(prefix="/api/v1/tutor", tags=["Tutor"])


@router.get("/lessons", response_model=list[LessonSummary])
def lessons(
    subject_code: str | None = Query(default=None, max_length=32),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return list_lessons(subject_code)


@router.get("/profile", response_model=TutorProfileResponse)
def profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return get_profile(db, user_id)


@router.put("/profile", response_model=TutorProfileResponse)
def update_profile(
    payload: TutorProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return save_profile(db, user_id, payload)


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: SessionCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return create_session(db, user_id, payload.subject_code, payload.curriculum_version)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def session(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return get_session(db, user_id, session_id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageView])
def session_messages(
    session_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    learning_session = get_session(db, user_id, session_id)
    return learning_session.messages


@router.post("/sessions/{session_id}/messages", response_model=MessageExchange)
def message(
    session_id: str,
    payload: MessageCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    learning_session = get_session(db, user_id, session_id)
    (
        learner_message,
        tutor_message,
        answer_status,
        source_lesson_id,
        source_title,
        answer_content,
    ) = append_message(
        db, learning_session, payload.content, payload.lesson_id, payload.locale
    )
    return MessageExchange(
        learner_message=MessageView.model_validate(learner_message),
        tutor_message=MessageView.model_validate(tutor_message) if tutor_message else None,
        answer=TutorAnswer(
            status=answer_status,
            content=answer_content,
            source_lesson_id=source_lesson_id,
            source_title=source_title,
        ),
    )
