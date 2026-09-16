from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class AgentState:
    """
    Current state of Ahmed AI execution.
    """

    user_request: str = ""

    intent: str = ""

    selected_agent: str = ""

    current_step: str = ""

    requires_approval: bool = False

    completed_steps: List[str] = field(default_factory=list)

    context: Dict[str, Any] = field(default_factory=dict)

    result: str = ""


    def add_step(self, step: str):
        self.completed_steps.append(step)


    def update_context(self, key: str, value: Any):
        self.context[key] = value


    def summary(self):
        return {
            "request": self.user_request,
            "intent": self.intent,
            "agent": self.selected_agent,
            "step": self.current_step,
            "approval_required": self.requires_approval,
            "completed_steps": self.completed_steps,
            "result": self.result,
        }
