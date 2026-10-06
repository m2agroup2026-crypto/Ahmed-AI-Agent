from fastapi import APIRouter

from .schemas import (
    LearningPathRequest,
    LearningPathResponse,
)
from .service import LearningPathService


router = APIRouter(
    prefix="/learning-path",
    tags=["Tutor Learning Path"],
)

service = LearningPathService()


@router.post(
    "/generate",
    response_model=LearningPathResponse,
)
def generate_learning_path(
    request: LearningPathRequest,
):

    return service.create_plan(
        request.weaknesses,
        request.recommended_topics,
    )
