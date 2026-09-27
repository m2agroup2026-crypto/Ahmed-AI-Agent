from fastapi import APIRouter

from .service import NexoraResponseService


router = APIRouter(
    prefix="/response",
    tags=["Tutor Response Intelligence"],
)

service = NexoraResponseService()


@router.post("/generate")
def generate_response(
    teaching_mode: str,
    skill: str,
    student_state: str = "normal",
):
    return service.create_response(
        teaching_mode,
        skill,
        student_state,
    )
