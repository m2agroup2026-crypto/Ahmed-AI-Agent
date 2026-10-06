from dataclasses import dataclass
from datetime import datetime


@dataclass
class NexoraEvent:
    event_type: str
    student_id: int
    payload: dict
    created_at: datetime


class EventTypes:

    STUDENT_RESPONSE = "student_response"

    LEARNING_EVALUATED = "learning_evaluated"

    TEACHING_DECISION = "teaching_decision"

    EXPERIENCE_UPDATED = "experience_updated"
