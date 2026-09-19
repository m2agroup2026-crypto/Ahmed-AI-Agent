from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class AIEvent:

    event_type: str

    user_id: int

    intent: str

    status: str

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventLogger:


    def __init__(self):

        self.events = []


    def log(
        self,
        event: AIEvent
    ):

        self.events.append(event)

        return event


    def all(self):

        return self.events
