from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Experience:
    """
    Represents a learned experience from Ahmed AI agents.
    """

    agent: str
    project: str
    task: str
    decision: str
    outcome: str
    lesson: str

    tags: list = field(default_factory=list)

    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )


    def summarize(self):

        return {
            "agent": self.agent,
            "project": self.project,
            "task": self.task,
            "decision": self.decision,
            "outcome": self.outcome,
            "lesson": self.lesson,
            "tags": self.tags,
            "created_at": self.created_at
        }
