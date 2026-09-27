from dataclasses import dataclass


@dataclass
class LearningEvaluation:
    success: bool
    progress_level: str
    recommendation: str


class EvaluationEngine:

    def evaluate(
        self,
        result: str,
        confidence: float,
    ) -> LearningEvaluation:

        if result == "correct" and confidence >= 0.8:
            return LearningEvaluation(
                success=True,
                progress_level="strong",
                recommendation="increase_learning_challenge",
            )

        if result == "correct":
            return LearningEvaluation(
                success=True,
                progress_level="improving",
                recommendation="continue_practice",
            )

        if confidence < 0.4:
            return LearningEvaluation(
                success=False,
                progress_level="struggling",
                recommendation="change_explanation_strategy",
            )

        return LearningEvaluation(
            success=False,
            progress_level="needs_practice",
            recommendation="provide_more_examples",
        )
