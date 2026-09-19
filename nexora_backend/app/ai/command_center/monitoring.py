from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class SystemHealth:

    component: str

    status: str

    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class MonitoringEngine:


    def check(
        self,
        component
    ):

        return SystemHealth(
            component,
            "healthy"
        )
