from dataclasses import dataclass


@dataclass
class InteractionDecision:

    action: str
    explanation_mode: str
    engagement_strategy: str


class InteractionEngine:

    def decide(
        self,
        emotion: str,
        recommended_style: str,
    ) -> InteractionDecision:

        if emotion == "frustrated":
            return InteractionDecision(
                action="explain",
                explanation_mode="simple_steps",
                engagement_strategy="restore_confidence",
            )

        if emotion == "confident":
            return InteractionDecision(
                action="challenge",
                explanation_mode="deep_reasoning",
                engagement_strategy="increase_growth",
            )

        if emotion == "progressing":
            return InteractionDecision(
                action="practice",
                explanation_mode="guided_examples",
                engagement_strategy="maintain_momentum",
            )

        return InteractionDecision(
            action="adapt",
            explanation_mode="adaptive",
            engagement_strategy="understand_student",
        )
