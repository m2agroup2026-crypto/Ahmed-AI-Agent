from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user_id
from app.api.auth.permission_dependencies import require_permission
from app.database.dependencies import get_db
from app.products.tutor.content import list_lessons
from app.products.tutor.importer import import_curriculum_bundle
from app.products.tutor.practice import get_next_question, submit_attempt
from app.products.tutor.progress import get_progress
from app.products.tutor.schemas import (
    CurriculumImportPayload,
    CurriculumImportResult,
    LessonSummary,
    MessageCreate,
    MessageExchange,
    MessageView,
    PracticeAttemptCreate,
    PracticeAttemptResponse,
    PracticeQuestionResponse,
    ProgressResponse,
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
    curriculum_version: str | None = Query(default=None, max_length=64),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return list_lessons(db, subject_code, curriculum_version)


@router.post(
    "/curriculum/import",
    response_model=CurriculumImportResult,
    status_code=status.HTTP_201_CREATED,
)
def import_curriculum(
    payload: CurriculumImportPayload,
    _: bool = Depends(require_permission("dashboard.manage")),
    db: Session = Depends(get_db),
):
    """Import a reviewed official bundle; learner APIs remain read-only."""

    return import_curriculum_bundle(db, payload)


@router.get("/practice/next", response_model=PracticeQuestionResponse)
def next_practice_question(
    subject_code: str = Query(..., min_length=1, max_length=32),
    curriculum_version: str = Query(default="egypt-secondary-2026", max_length=64),
    lesson_id: str | None = Query(default=None, max_length=128),
    skill_code: str | None = Query(default=None, max_length=128),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return get_next_question(
        db,
        user_id,
        subject_code,
        curriculum_version,
        lesson_id,
        skill_code,
    )


@router.post("/practice/attempts", response_model=PracticeAttemptResponse, status_code=status.HTTP_201_CREATED)
def practice_attempt(
    payload: PracticeAttemptCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    result = submit_attempt(
        db,
        user_id,
        payload.question_id,
        payload.submitted_answer,
        payload.locale,
        payload.session_id,
    )
    return PracticeAttemptResponse(
        attempt_id=result.attempt_id,
        question_id=result.question_id,
        is_correct=result.is_correct,
        score=result.score,
        max_score=result.max_score,
        explanation_ar=result.explanation_ar,
        explanation_en=result.explanation_en,
        source_url=result.source_url,
        source_locator=result.source_locator,
        next_action=result.next_action,
    )


@router.get("/progress", response_model=ProgressResponse)
def progress(
    curriculum_version: str | None = Query(default=None, max_length=64),
    subject_code: str | None = Query(default=None, max_length=32),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    require_active_user(db, user_id)
    return get_progress(db, user_id, curriculum_version, subject_code)


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
        source_url,
        source_locator,
        adaptation_mode,
        next_action,
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
            source_url=source_url,
            source_locator=source_locator,
            adaptation_mode=adaptation_mode,
            next_action=next_action,
        ),
    )
