from .generator import ResponseGenerator
from .templates import get_template


class NexoraResponseService:

    def __init__(self):
        self.generator = ResponseGenerator()

    def create_response(
        self,
        teaching_mode: str,
        skill: str,
        student_state: str = "normal",
    ):

        response = self.generator.generate(
            teaching_mode,
            skill,
            student_state,
        )

        template = get_template(
            response.emotional_tone
        )

        return {
            "message": response.message,
            "opening": template["opening"],
            "teaching_action": response.teaching_action,
            "emotional_tone": response.emotional_tone,
            "style": template["style"],
            "next_step": response.next_step,
        }
