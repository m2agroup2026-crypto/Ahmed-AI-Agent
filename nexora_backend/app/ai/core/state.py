from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentState:

    user_id: int

    input_text: str

    intent: str | None = None

    permission: str | None = None

    status: str = "initialized"

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )
