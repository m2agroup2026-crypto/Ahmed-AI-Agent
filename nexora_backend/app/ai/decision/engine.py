from app.ai.decision.trace import DecisionTrace


class DecisionEngine:


    def evaluate(
        self,
        allowed: bool,
        reason: str
    ):

        if allowed:

            return DecisionTrace(
                decision="ALLOW",
                reason=reason,
                status="approved"
            )


        return DecisionTrace(
            decision="DENY",
            reason=reason,
            status="rejected"
        )
