from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class AIAlert:

    level: str

    message: str

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AlertEngine:


    def __init__(self):

        self.alerts = []


    def create(
        self,
        level,
        message
    ):

        alert = AIAlert(
            level,
            message
        )

        self.alerts.append(alert)

        return alert


    def all(self):

        return self.alerts
