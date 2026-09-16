class ToolPermissionGateway:
    """
    Controls whether Ahmed AI can execute a tool.
    """


    RISK_LEVELS = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4
    }


    def __init__(self, approval_required=False):
        self.approval_required = approval_required


    def check(self, tool_definition):

        risk = tool_definition.get(
            "risk_level",
            "low"
        )

        requires_approval = tool_definition.get(
            "requires_approval",
            False
        )


        if risk in ["high", "critical"]:

            if requires_approval:
                return {
                    "allowed": False,
                    "reason": "Human approval required"
                }


        return {
            "allowed": True,
            "reason": "Permission granted"
        }
