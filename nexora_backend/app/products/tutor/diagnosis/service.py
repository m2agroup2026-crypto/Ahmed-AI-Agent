from .engine import DiagnosisEngine


class DiagnosisService:

    def __init__(self):
        self.engine = DiagnosisEngine()

    def create_profile(self, answers: list[dict]):

        result = self.engine.analyze(
            answers
        )

        return {
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommended_topics": result.recommended_topics,
        }
