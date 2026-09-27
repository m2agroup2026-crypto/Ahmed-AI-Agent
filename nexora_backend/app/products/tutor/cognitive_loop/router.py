from fastapi import APIRouter

from .service import NexoraCognitiveService


router = APIRouter(
    prefix="/cognitive-loop",
    tags=["Tutor Cognitive Loop"],
)

service = NexoraCognitiveService()


@router.post("/analyze")
def analyze_learning_event(
    student_id: int,
    skill: str,
    action: str,
    result: str,
    confidence: float = 0.0,
):
    return service.analyze_learning_event(
        student_id,
        skill,
        action,
        result,
        confidence,
    )
