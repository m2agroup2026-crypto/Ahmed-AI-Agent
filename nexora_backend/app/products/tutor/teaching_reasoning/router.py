from fastapi import APIRouter

from .service import TeachingReasoningService


router = APIRouter(
    prefix="/teaching-reasoning",
    tags=["Tutor Teaching Reasoning"],
)

service = TeachingReasoningService()


@router.post("/analyze")
def analyze_teaching_response(
    correct: bool,
    attempts: int,
    skill: str,
):
    return service.analyze_response(
        correct,
        attempts,
        skill,
    )
