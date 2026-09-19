from fastapi import APIRouter
from app.api.ai.schemas import AIRequest, AIResponse


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/execute",
    response_model=AIResponse
)
def execute_ai(
    request: AIRequest
):

    return AIResponse(
        intent="PROCESSING",
        decision="PENDING",
        status="received"
    )
