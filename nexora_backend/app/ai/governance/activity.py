from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIActivity:

    user_id: int

    activity: str

    status: str

    created_at: datetime = datetime.utcnow()


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
