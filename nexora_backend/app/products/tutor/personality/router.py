from fastapi import APIRouter

from .service import NexoraPersonalityService


router = APIRouter(
    prefix="/personality",
    tags=["Tutor Personality"],
)

service = NexoraPersonalityService()


@router.get("/profile")
def personality_profile(
    student_state: str = "normal",
):
    return service.get_profile(
        student_state
    )
