from dataclasses import dataclass


@dataclass
class NexoraState:
    phase: str
    student_condition: str
    teaching_goal: str
    confidence: float = 0.0


DEFAULT_STATE = NexoraState(
    phase="understanding",
    student_condition="unknown",
    teaching_goal="identify_learning_need",
    confidence=0.0,
)


VALID_PHASES = [
    "understanding",
    "analyzing",
    "planning",
    "teaching",
    "evaluating",
    "adapting",
]
