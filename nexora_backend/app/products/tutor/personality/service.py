from .profile import DEFAULT_PERSONALITY
from .behavior import get_behavior


class NexoraPersonalityService:

    def get_profile(
        self,
        student_state: str = "normal",
    ):

        behavior = get_behavior(
            student_state
        )

        return {
            "name": DEFAULT_PERSONALITY.name,
            "role": DEFAULT_PERSONALITY.role,
            "tone": DEFAULT_PERSONALITY.tone,
            "teaching_style": DEFAULT_PERSONALITY.teaching_style,
            "motivation_style": DEFAULT_PERSONALITY.motivation_style,
            "behavior": {
                "response_style": behavior.response_style,
                "encouragement_level": behavior.encouragement_level,
                "explanation_depth": behavior.explanation_depth,
                "adaptation_mode": behavior.adaptation_mode,
            },
        }
