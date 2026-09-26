from dataclasses import dataclass, field


@dataclass
class StudentContext:
    student_id: int
    learning_state: str
    current_subject: str | None = None
    current_skill: str | None = None
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recent_events: list[dict] = field(default_factory=list)
    personality_mode: str = "adaptive"


class ContextBuilder:

    def build(
        self,
        student_id: int,
        learning_state: str,
        current_subject: str | None = None,
        current_skill: str | None = None,
        strengths: list[str] | None = None,
        weaknesses: list[str] | None = None,
        recent_events: list[dict] | None = None,
        personality_mode: str = "adaptive",
    ) -> StudentContext:

        return StudentContext(
            student_id=student_id,
            learning_state=learning_state,
            current_subject=current_subject,
            current_skill=current_skill,
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            recent_events=recent_events or [],
            personality_mode=personality_mode,
        )
