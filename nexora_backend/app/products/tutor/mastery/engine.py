from .scoring import MasteryScoringEngine
from .levels import get_level


class NexoraMasteryEngine:


    def __init__(self):

        self.scoring_engine = (
            MasteryScoringEngine()
        )


    def evaluate(

        self,

        knowledge: float,

        consistency: float,

        problem_solving: float,

        creativity: float,

        curiosity: float,

    ):


        score = self.scoring_engine.calculate(

            knowledge,

            consistency,

            problem_solving,

            creativity,

            curiosity,

        )


        level = get_level(
            score.total
        )


        return {

            "mastery_score": score.total,

            "level": level.name,

            "unlocks": level.unlocks,

            "profile": {

                "knowledge": score.knowledge,

                "consistency": score.consistency,

                "problem_solving": score.problem_solving,

                "creativity": score.creativity,

                "curiosity": score.curiosity,

            }

        }
