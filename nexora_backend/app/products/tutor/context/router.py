from fastapi import APIRouter

from .service import NexoraContextService


router = APIRouter(
    prefix="/context",
    tags=["Tutor Context"],
)

service = NexoraContextService()


@router.post("/build")
def build_context(
    student_id: int,
    learning_state: str,
    current_subject: str | None = None,
    current_skill: str | None = None,
    personality_mode: str = "adaptive",
):
    return service.create_context(
        student_id=student_id,
        learning_state=learning_state,
        current_subject=current_subject,
        current_skill=current_skill,
        personality_mode=personality_mode,
    )
