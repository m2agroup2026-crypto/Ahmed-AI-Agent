from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemHealth:

    component: str

    status: str

    checked_at: datetime = datetime.utcnow()


class MonitoringEngine:


    def check(
        self,
        component
    ):

        return SystemHealth(
            component,
            "healthy"
        )
