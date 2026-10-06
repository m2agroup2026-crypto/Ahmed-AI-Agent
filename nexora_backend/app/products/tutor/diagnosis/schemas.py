from pydantic import BaseModel


class DiagnosisAnswer(BaseModel):
    skill: str
    correct: bool


class DiagnosisRequest(BaseModel):
    answers: list[DiagnosisAnswer]


class LearningProfileResponse(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    recommended_topics: list[str]
