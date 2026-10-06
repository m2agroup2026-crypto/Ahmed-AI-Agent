from dataclasses import dataclass


@dataclass
class NexoraResponse:
    message: str
    teaching_action: str
    emotional_tone: str
    next_step: str


class ResponseGenerator:

    def generate(
        self,
        teaching_mode: str,
        skill: str,
        student_state: str = "normal",
    ) -> NexoraResponse:

        if teaching_mode == "simplified_explanation":
            return NexoraResponse(
                message=f"Let's understand {skill} step by step in a simpler way.",
                teaching_action="explain_foundation",
                emotional_tone="supportive",
                next_step="review_concept",
            )

        if teaching_mode == "guided_examples":
            return NexoraResponse(
                message=f"Let's practice {skill} together with a guided example.",
                teaching_action="guided_practice",
                emotional_tone="encouraging",
                next_step="solve_example",
            )

        if teaching_mode == "challenge":
            return NexoraResponse(
                message=f"Great progress. Let's test your advanced understanding of {skill}.",
                teaching_action="advanced_challenge",
                emotional_tone="motivating",
                next_step="attempt_harder_problem",
            )

        return NexoraResponse(
            message=f"Let's continue improving your {skill}.",
            teaching_action="adaptive_support",
            emotional_tone="positive",
            next_step="continue_learning",
        )
