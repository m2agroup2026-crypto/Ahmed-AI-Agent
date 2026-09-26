from dataclasses import dataclass
from datetime import datetime


@dataclass
class LearningEvent:
    student_id: int
    event_type: str
    subject: str
    skill: str
    result: str
    created_at: datetime
