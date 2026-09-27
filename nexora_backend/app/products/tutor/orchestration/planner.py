from dataclasses import dataclass


@dataclass
class TeachingPlan:
    action: str
    priority: str
    reason: str


class NexoraPlanner:

    def create_plan(
        self,
        student_condition: str,
        learning_goal: str,
    ) -> TeachingPlan:

        if student_condition == "struggling":
            return TeachingPlan(
                action="simplify_and_explain",
                priority="high",
                reason="student needs foundation support",
            )

        if student_condition == "improving":
            return TeachingPlan(
                action="guided_practice",
                priority="medium",
                reason="student needs reinforcement",
            )

        if student_condition == "advanced":
            return TeachingPlan(
                action="challenge_student",
                priority="high",
                reason="student is ready for deeper learning",
            )

        return TeachingPlan(
            action="analyze_learning_need",
            priority="normal",
            reason=learning_goal,
        )
