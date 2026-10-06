from .engine import AdaptiveTeachingEngine


class AdaptiveTeachingService:

    def __init__(self):
        self.engine = AdaptiveTeachingEngine()

    def adapt(
        self,
        issue_type: str,
        progress_score: float,
    ):

        decision = self.engine.decide(
            issue_type,
            progress_score,
        )

        return {
            "next_level": decision.next_level,
            "teaching_mode": decision.teaching_mode,
            "recommendation": decision.recommendation,
        }
