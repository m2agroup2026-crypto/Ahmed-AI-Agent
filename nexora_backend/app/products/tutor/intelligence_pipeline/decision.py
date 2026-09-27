from dataclasses import dataclass


@dataclass
class NexoraDecision:

    action: str

    response_mode: str

    priority: str

    reason: str



class DecisionEngine:


    def decide(
        self,
        context,
    ) -> NexoraDecision:


        if (
            context.emotion == "frustrated"
            or context.learning_state == "struggling"
        ):

            return NexoraDecision(
                action="support_student",
                response_mode="simple_explanation",
                priority="high",
                reason="student needs confidence recovery",
            )


        if (
            context.emotion == "confident"
            and context.learning_state == "strong"
        ):

            return NexoraDecision(
                action="challenge_student",
                response_mode="deep_reasoning",
                priority="high",
                reason="student is ready for advanced learning",
            )


        if context.learning_state == "improving":

            return NexoraDecision(
                action="guided_practice",
                response_mode="guided_examples",
                priority="medium",
                reason="student needs reinforcement",
            )


        return NexoraDecision(
            action="adaptive_teaching",
            response_mode="adaptive",
            priority="normal",
            reason="continue understanding student",
        )
