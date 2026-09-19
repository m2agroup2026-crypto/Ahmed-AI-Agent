from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIAlert:

    level: str

    message: str

    created_at: datetime = datetime.utcnow()


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
