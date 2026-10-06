from fastapi import APIRouter

from .service import NexoraMemoryService


router = APIRouter(
    prefix="/memory",
    tags=["Tutor Memory"],
)

service = NexoraMemoryService()


@router.post("/remember")
def remember_event(
    student_id: int,
    event_type: str,
    subject: str,
    skill: str,
    result: str,
):
    return service.remember(
        student_id,
        event_type,
        subject,
        skill,
        result,
    )


@router.get("/{student_id}")
def recall_history(
    student_id: int,
):
    return service.recall(
        student_id
    )
