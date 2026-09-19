from pydantic import BaseModel


class AIRequest(BaseModel):

    user_id: int

    command: str



class AIResponse(BaseModel):

    intent: str

    decision: str

    status: str
