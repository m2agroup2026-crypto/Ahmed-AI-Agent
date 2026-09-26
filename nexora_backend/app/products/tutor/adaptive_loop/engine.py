from dataclasses import dataclass


@dataclass
class AdaptiveDecision:
    next_level: str
    teaching_mode: str
    recommendation: str


class AdaptiveTeachingEngine:

    def decide(
        self,
        issue_type: str,
        progress_score: float,
    ) -> AdaptiveDecision:

        if issue_type == "concept_gap":
            return AdaptiveDecision(
                next_level="foundation",
                teaching_mode="simplified_explanation",
                recommendation="review concept before new practice",
            )

        if issue_type == "practice_gap":
            return AdaptiveDecision(
                next_level="practice",
                teaching_mode="guided_examples",
                recommendation="increase targeted exercises",
            )

        if progress_score >= 0.85:
            return AdaptiveDecision(
                next_level="advanced",
                teaching_mode="challenge",
                recommendation="introduce advanced problems",
            )

        return AdaptiveDecision(
            next_level="current",
            teaching_mode="balanced",
            recommendation="continue personalized practice",
        )
