from .engine import NexoraOrchestrationEngine
from .state import NexoraState


class NexoraOrchestrationService:

    def __init__(self):
        self.engine = NexoraOrchestrationEngine()

    def process(
        self,
        phase: str,
        student_condition: str,
        teaching_goal: str,
        confidence: float = 0.0,
    ):

        state = NexoraState(
            phase=phase,
            student_condition=student_condition,
            teaching_goal=teaching_goal,
            confidence=confidence,
        )

        return self.engine.think(
            state
        )
