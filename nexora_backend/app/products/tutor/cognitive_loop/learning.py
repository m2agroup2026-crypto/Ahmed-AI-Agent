from dataclasses import dataclass, field


@dataclass
class StudentLearningModel:
    student_id: int
    learned_skills: list[str] = field(default_factory=list)
    difficult_skills: list[str] = field(default_factory=list)
    preferred_strategy: str = "adaptive"


class LearningEngine:

    def update(
        self,
        student_id: int,
        skill: str,
        evaluation,
    ) -> StudentLearningModel:

        model = StudentLearningModel(
            student_id=student_id,
        )

        if evaluation.success:
            model.learned_skills.append(skill)

        else:
            model.difficult_skills.append(skill)
            model.preferred_strategy = (
                evaluation.recommendation
            )

        return model
