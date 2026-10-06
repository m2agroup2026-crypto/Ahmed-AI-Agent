from .analyzer import TeachingReasoningAnalyzer
from .strategies import get_strategy


class TeachingReasoningService:

    def __init__(self):
        self.analyzer = TeachingReasoningAnalyzer()

    def analyze_response(
        self,
        correct: bool,
        attempts: int,
        skill: str,
    ):

        insight = self.analyzer.analyze(
            correct,
            attempts,
            skill,
        )

        strategy = get_strategy(
            insight.issue_type
        )

        return {
            "issue_type": insight.issue_type,
            "explanation_strategy": strategy["method"],
            "strategy_description": strategy["description"],
            "next_action": insight.next_action,
        }
