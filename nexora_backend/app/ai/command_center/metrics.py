from dataclasses import dataclass


@dataclass
class AIMetrics:

    total_requests: int

    approved_actions: int

    rejected_actions: int

    system_status: str


class MetricsCollector:


    def collect(
        self,
        events
    ):

        total = len(events)

        approved = len(
            [
                e for e in events
                if e.status == "approved"
            ]
        )

        rejected = total - approved


        return AIMetrics(
            total,
            approved,
            rejected,
            "healthy"
        )
