from dataclasses import dataclass


@dataclass
class MasteryScore:

    total: int

    knowledge: float

    consistency: float

    problem_solving: float

    creativity: float

    curiosity: float



class MasteryScoringEngine:


    def calculate(

        self,

        knowledge: float,

        consistency: float,

        problem_solving: float,

        creativity: float,

        curiosity: float,

    ) -> MasteryScore:


        total = int(

            knowledge * 0.35

            + consistency * 0.20

            + problem_solving * 0.25

            + creativity * 0.10

            + curiosity * 0.10

        )


        return MasteryScore(

            total=total,

            knowledge=knowledge,

            consistency=consistency,

            problem_solving=problem_solving,

            creativity=creativity,

            curiosity=curiosity,

        )
