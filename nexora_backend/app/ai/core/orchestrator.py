from app.ai.core.fabric import IntelligenceFabric
from app.ai.governance.audit import AuditLogger, AuditRecord
from app.ai.billing.action_mapper import map_action
from app.ai.integration.billing_adapter import BillingAdapter


class NexoraOrchestrator:


    def __init__(self):

        self.fabric = IntelligenceFabric()

        self.audit = AuditLogger()

        self.billing = BillingAdapter()


    def run(
        self,
        db,
        user_id: int,
        text: str
    ):

        agent = self.fabric.resolve_agent()


        result = agent.process(
            db,
            user_id,
            text
        )


        decision = result["decision"]


        action = map_action(
            result["state"].intent
        )


        self.billing.charge_ai_action(
            user_id,
            action
        )


        self.audit.record(
            AuditRecord(
                user_id,
                result["state"].intent,
                decision.decision,
                decision.reason
            )
        )


        return result
