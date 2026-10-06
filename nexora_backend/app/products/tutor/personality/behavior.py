from dataclasses import dataclass


@dataclass
class NexoraBehavior:
    response_style: str
    encouragement_level: str
    explanation_depth: str
    adaptation_mode: str


def get_behavior(student_state: str) -> NexoraBehavior:

    if student_state == "struggling":
        return NexoraBehavior(
            response_style="supportive",
            encouragement_level="high",
            explanation_depth="simple",
            adaptation_mode="foundation",
        )

    if student_state == "advanced":
        return NexoraBehavior(
            response_style="challenging",
            encouragement_level="balanced",
            explanation_depth="deep",
            adaptation_mode="advanced",
        )

    return NexoraBehavior(
        response_style="adaptive",
        encouragement_level="positive",
        explanation_depth="medium",
        adaptation_mode="personalized",
    )
