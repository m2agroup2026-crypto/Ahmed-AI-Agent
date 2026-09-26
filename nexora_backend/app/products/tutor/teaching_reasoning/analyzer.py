from dataclasses import dataclass


@dataclass
class TeachingInsight:
    issue_type: str
    explanation_strategy: str
    next_action: str


class TeachingReasoningAnalyzer:

    def analyze(
        self,
        correct: bool,
        attempts: int,
        skill: str,
    ) -> TeachingInsight:

        if correct:
            return TeachingInsight(
                issue_type="mastered",
                explanation_strategy="advanced_practice",
                next_action=f"challenge student on {skill}",
            )

        if attempts > 2:
            return TeachingInsight(
                issue_type="concept_gap",
                explanation_strategy="simplified_explanation",
                next_action=f"review fundamentals of {skill}",
            )

        return TeachingInsight(
            issue_type="practice_gap",
            explanation_strategy="guided_example",
            next_action=f"provide example for {skill}",
        )
