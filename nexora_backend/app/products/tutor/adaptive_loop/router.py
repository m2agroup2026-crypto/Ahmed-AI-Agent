from fastapi import APIRouter

from .service import AdaptiveTeachingService


router = APIRouter(
    prefix="/adaptive-loop",
    tags=["Tutor Adaptive Loop"],
)

service = AdaptiveTeachingService()


@router.post("/decide")
def adaptive_decision(
    issue_type: str,
    progress_score: float,
):
    return service.adapt(
        issue_type,
        progress_score,
    )
