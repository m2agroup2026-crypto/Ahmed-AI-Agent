from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class AIActivity:

    user_id: int

    activity: str

    status: str

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ActivityTracker:


    def __init__(self):

        self.activities = []


    def add(
        self,
        activity: AIActivity
    ):

        self.activities.append(activity)

        return activity


    def timeline(self):

        return self.activities
