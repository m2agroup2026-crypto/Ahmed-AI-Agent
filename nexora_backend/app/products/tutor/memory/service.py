from datetime import datetime

from .events import LearningEvent
from .store import MemoryStore


class NexoraMemoryService:

    def __init__(self):
        self.store = MemoryStore()

    def remember(
        self,
        student_id: int,
        event_type: str,
        subject: str,
        skill: str,
        result: str,
    ):

        event = LearningEvent(
            student_id=student_id,
            event_type=event_type,
            subject=subject,
            skill=skill,
            result=result,
            created_at=datetime.utcnow(),
        )

        return self.store.save(event)

    def recall(
        self,
        student_id: int,
    ):

        return self.store.get_student_history(
            student_id
        )
