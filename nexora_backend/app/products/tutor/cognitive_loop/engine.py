from .observation import ObservationEngine
from .evaluation import EvaluationEngine
from .learning import LearningEngine


class NexoraCognitiveEngine:

    def __init__(self):
        self.observation_engine = ObservationEngine()
        self.evaluation_engine = EvaluationEngine()
        self.learning_engine = LearningEngine()

    def process(
        self,
        student_id: int,
        skill: str,
        action: str,
        result: str,
        confidence: float = 0.0,
    ):

        observation = self.observation_engine.observe(
            student_id,
            skill,
            action,
            result,
            confidence,
        )

        evaluation = self.evaluation_engine.evaluate(
            result,
            confidence,
        )

        learning_model = self.learning_engine.update(
            student_id,
            skill,
            evaluation,
        )

        return {
            "observation": {
                "skill": observation.skill,
                "action": observation.action,
                "result": observation.result,
            },
            "evaluation": {
                "success": evaluation.success,
                "progress_level": evaluation.progress_level,
                "recommendation": evaluation.recommendation,
            },
            "learning": {
                "learned_skills": learning_model.learned_skills,
                "difficult_skills": learning_model.difficult_skills,
                "preferred_strategy": learning_model.preferred_strategy,
            },
        }
