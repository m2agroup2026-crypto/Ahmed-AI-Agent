from .engine import LearningPathEngine


class LearningPathService:

    def __init__(self):
        self.engine = LearningPathEngine()

    def create_plan(
        self,
        weaknesses: list[str],
        recommended_topics: list[str],
    ):

        plan = self.engine.build(
            weaknesses,
            recommended_topics,
        )

        return {
            "priority_topics": plan.priority_topics,
            "daily_steps": plan.daily_steps,
        }
