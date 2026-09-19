from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class DecisionTrace:

    decision: str

    reason: str

    status: str

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
