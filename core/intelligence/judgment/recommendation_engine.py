class RecommendationEngine:
    """
    Generates professional recommendations from analysis and risks.
    """


    def generate(self, decision_analysis, risk_analysis):

        options = decision_analysis.get(
            "options",
            []
        )


        selected = (
            options[0]
            if options
            else None
        )


        return {
            "recommended_option": selected,
            "reason": "Recommendation generated from decision analysis and risk evaluation",
            "risks": risk_analysis.get(
                "risks",
                []
            ),
            "confidence": "initial"
        }
