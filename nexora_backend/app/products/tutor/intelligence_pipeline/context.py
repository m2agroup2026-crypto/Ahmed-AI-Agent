from dataclasses import dataclass, field


@dataclass
class NexoraContext:

    student_id: int

    skill: str

    learning_state: str

    recommendation: str

    emotion: str

    teaching_style: str

    confidence: float = 0.0

    metadata: dict = field(
        default_factory=dict
    )


class ContextAssembler:

    def build(
        self,
        student_id: int,
        skill: str,
        cognitive_result: dict,
        experience_result: dict,
        confidence: float = 0.0,
    ) -> NexoraContext:

        evaluation = cognitive_result.get(
            "evaluation",
            {},
        )

        emotion = experience_result.get(
            "emotion",
            {},
        )

        return NexoraContext(

            student_id=student_id,

            skill=skill,

            learning_state=evaluation.get(
                "progress_level",
                "unknown",
            ),

            recommendation=evaluation.get(
                "recommendation",
                "continue_learning",
            ),

            emotion=emotion.get(
                "state",
                "neutral",
            ),

            teaching_style=emotion.get(
                "style",
                "adaptive",
            ),

            confidence=confidence,

            metadata={
                "cognitive": cognitive_result,
                "experience": experience_result,
            },
        )
