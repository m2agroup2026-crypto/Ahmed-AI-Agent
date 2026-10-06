from .engine import NexoraMasteryEngine
from .unlock import NexoraUnlockEngine


class NexoraMasteryService:


    def __init__(self):

        self.mastery_engine = NexoraMasteryEngine()

        self.unlock_engine = NexoraUnlockEngine()



    def evaluate_student(

        self,

        student_id: int,

        knowledge: float,

        consistency: float,

        problem_solving: float,

        creativity: float,

        curiosity: float,

    ):


        mastery = self.mastery_engine.evaluate(

            knowledge,

            consistency,

            problem_solving,

            creativity,

            curiosity,

        )


        access = self.unlock_engine.unlock(

            student_id,

            mastery["level"],

        )


        mastery_profile = {

            "mastery_score": mastery["mastery_score"],

            "level": mastery["level"],

            "profile": mastery["profile"],

        }


        return {

            "student_id": student_id,

            "mastery": mastery_profile,

            "access": access,

        }
