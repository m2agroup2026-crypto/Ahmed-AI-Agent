from dataclasses import dataclass


@dataclass
class ExperienceState:

    student_id: int

    emotion: str = "neutral"

    engagement_level: str = "normal"

    interaction_mode: str = "conversation"

    confidence_level: float = 0.0

    attention_level: float = 0.0


DEFAULT_EXPERIENCE = ExperienceState(
    student_id=0,
    emotion="neutral",
    engagement_level="normal",
    interaction_mode="conversation",
    confidence_level=0.0,
    attention_level=0.0,
)
