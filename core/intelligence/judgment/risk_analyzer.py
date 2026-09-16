class RiskAnalyzer:
    """
    Analyzes possible risks in decisions.
    """


    def analyze(self, option):

        risks = []


        option_lower = option.lower()


        if "microservice" in option_lower:

            risks.extend([
                "Higher system complexity",
                "More deployment overhead"
            ])


        if "mongodb" in option_lower:

            risks.extend([
                "Complex relational queries",
                "Data consistency considerations"
            ])


        if "postgresql" in option_lower:

            risks.extend([
                "Schema changes require planning"
            ])


        if not risks:

            risks.append(
                "General implementation risks should be evaluated"
            )


        return {
            "option": option,
            "risks": risks
        }
