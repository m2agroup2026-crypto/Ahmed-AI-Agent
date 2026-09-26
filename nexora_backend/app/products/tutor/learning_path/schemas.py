from pydantic import BaseModel


class LearningPathRequest(BaseModel):
    weaknesses: list[str]
    recommended_topics: list[str]


class LearningPathResponse(BaseModel):
    priority_topics: list[str]
    daily_steps: list[str]
