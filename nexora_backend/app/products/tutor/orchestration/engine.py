from .planner import NexoraPlanner
from .state import NexoraState


class NexoraOrchestrationEngine:

    def __init__(self):
        self.planner = NexoraPlanner()

    def think(
        self,
        state: NexoraState,
    ):

        plan = self.planner.create_plan(
            state.student_condition,
            state.teaching_goal,
        )

        return {
            "current_phase": state.phase,
            "student_condition": state.student_condition,
            "confidence": state.confidence,
            "plan": {
                "action": plan.action,
                "priority": plan.priority,
                "reason": plan.reason,
            },
        }
