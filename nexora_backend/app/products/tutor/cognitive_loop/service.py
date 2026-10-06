from .engine import NexoraCognitiveEngine


class NexoraCognitiveService:

    def __init__(self):
        self.engine = NexoraCognitiveEngine()

    def analyze_learning_event(
        self,
        student_id: int,
        skill: str,
        action: str,
        result: str,
        confidence: float = 0.0,
    ):

        return self.engine.process(
            student_id,
            skill,
            action,
            result,
            confidence,
        )
