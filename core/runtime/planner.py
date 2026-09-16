class TaskPlanner:
    """
    Converts user goals into execution plans.
    """


    def create_plan(self, request: str):

        request = request.lower()

        if "start" in request or "شغل" in request:
            return [
                "Identify project",
                "Check environment",
                "Start required services",
                "Verify status",
                "Report result",
            ]


        if "review" in request or "راجع" in request:
            return [
                "Analyze files",
                "Check architecture",
                "Find issues",
                "Generate recommendations",
            ]


        return [
            "Understand request",
            "Analyze requirements",
            "Provide solution",
        ]
