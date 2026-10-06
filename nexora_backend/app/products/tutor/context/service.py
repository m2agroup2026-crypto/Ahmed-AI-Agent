from .builder import ContextBuilder


class NexoraContextService:

    def __init__(self):
        self.builder = ContextBuilder()

    def create_context(
        self,
        student_id: int,
        learning_state: str,
        current_subject: str | None = None,
        current_skill: str | None = None,
        strengths: list[str] | None = None,
        weaknesses: list[str] | None = None,
        recent_events: list[dict] | None = None,
        personality_mode: str = "adaptive",
    ):

        context = self.builder.build(
            student_id=student_id,
            learning_state=learning_state,
            current_subject=current_subject,
            current_skill=current_skill,
            strengths=strengths,
            weaknesses=weaknesses,
            recent_events=recent_events,
            personality_mode=personality_mode,
        )

        return {
            "student_id": context.student_id,
            "learning_state": context.learning_state,
            "current_subject": context.current_subject,
            "current_skill": context.current_skill,
            "strengths": context.strengths,
            "weaknesses": context.weaknesses,
            "recent_events": context.recent_events,
            "personality_mode": context.personality_mode,
        }
