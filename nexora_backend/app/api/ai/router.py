from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.ai.schemas import AIRequest, AIResponse
from app.database.dependencies import get_db
from app.api.auth.dependencies import get_current_user
from app.models.user import User
from app.ai.core.orchestrator import NexoraOrchestrator


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


orchestrator = NexoraOrchestrator()


@router.post(
    "/execute",
    response_model=AIResponse,
)
def execute_ai(
    request: AIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Transitional compatibility:
    # user_id may still be supplied by older clients, but it can
    # never establish identity. The JWT-derived user is authoritative.
    if (
        request.user_id is not None
        and request.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User identity mismatch",
        )

    result = orchestrator.run(
        db,
        current_user.id,
        request.command,
    )

    return AIResponse(
        intent=result["state"].intent,
        decision=result["decision"].decision,
        status=result["state"].status,
    )
