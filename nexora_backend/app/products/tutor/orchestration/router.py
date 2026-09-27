from fastapi import APIRouter

from .service import NexoraOrchestrationService


router = APIRouter(
    prefix="/orchestration",
    tags=["Tutor Orchestration"],
)

service = NexoraOrchestrationService()


@router.post("/think")
def nexora_think(
    phase: str,
    student_condition: str,
    teaching_goal: str,
    confidence: float = 0.0,
):
    return service.process(
        phase,
        student_condition,
        teaching_goal,
        confidence,
    )
