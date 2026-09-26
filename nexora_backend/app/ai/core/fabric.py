from app.ai.agents import registry
from app.ai.governance.audit import AuditLogger, AuditRecord
from app.ai.command_center.metrics import MetricsCollector


class IntelligenceFabric:


    def __init__(self):

        self.audit = AuditLogger()

        self.metrics = MetricsCollector()


    def resolve_agent(
        self,
        agent_name: str = "general"
    ):

        return registry.get(
            agent_name
        )


    def process(
        self,
        result
    ):

        state = result["state"]

        decision = result["decision"]


        audit = self.audit.record(
            AuditRecord(
                state.user_id,
                state.intent,
                decision.decision,
                decision.reason
            )
        )


        return {
            "result": result,
            "audit": audit
        }
