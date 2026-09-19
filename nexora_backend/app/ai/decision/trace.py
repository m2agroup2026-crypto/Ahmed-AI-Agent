from dataclasses import dataclass
from datetime import datetime


@dataclass
class DecisionTrace:

    decision: str

    reason: str

    status: str

    created_at: datetime = datetime.utcnow()
