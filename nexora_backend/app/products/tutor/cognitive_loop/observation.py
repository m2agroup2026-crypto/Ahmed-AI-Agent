from dataclasses import dataclass
from datetime import datetime


@dataclass
class LearningObservation:
    student_id: int
    skill: str
    action: str
    result: str
    confidence: float
    created_at: datetime


class ObservationEngine:

    def observe(
        self,
        student_id: int,
        skill: str,
        action: str,
        result: str,
        confidence: float = 0.0,
    ) -> LearningObservation:

        return LearningObservation(
            student_id=student_id,
            skill=skill,
            action=action,
            result=result,
            confidence=confidence,
            created_at=datetime.utcnow(),
        )
