from pydantic import BaseModel, ConfigDict


class AIRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    command: str
    user_id: int | None = None


class AIResponse(BaseModel):

    intent: str
    decision: str
    status: str
