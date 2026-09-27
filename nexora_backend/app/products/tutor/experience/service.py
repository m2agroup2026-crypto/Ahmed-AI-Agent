from .engine import NexoraExperienceEngine


class NexoraExperienceService:

    def __init__(self):
        self.engine = NexoraExperienceEngine()


    def build_experience(
        self,
        success: bool,
        confidence: float,
    ):

        return self.engine.create_experience(
            success,
            confidence,
        )
