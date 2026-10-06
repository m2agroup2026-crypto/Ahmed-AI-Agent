from fastapi import APIRouter

from .schemas import (
    DiagnosisRequest,
    LearningProfileResponse,
)
from .service import DiagnosisService


router = APIRouter(
    prefix="/diagnosis",
    tags=["Tutor Diagnosis"],
)

service = DiagnosisService()


@router.post(
    "/analyze",
    response_model=LearningProfileResponse,
)
def analyze_diagnosis(
    request: DiagnosisRequest,
):

    return service.create_profile(
        [
            answer.model_dump()
            for answer in request.answers
        ]
    )
