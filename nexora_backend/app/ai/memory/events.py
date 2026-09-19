from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIEvent:

    event_type: str

    user_id: int

    intent: str

    status: str

    created_at: datetime = datetime.utcnow()


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
