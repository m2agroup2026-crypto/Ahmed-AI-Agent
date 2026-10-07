from app.ai.core.fabric import IntelligenceFabric
from app.ai.governance.audit import AuditLogger, AuditRecord


class NexoraOrchestrator:


    def __init__(self):

        self.fabric = IntelligenceFabric()

        self.audit = AuditLogger()


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



        self.audit.record(
            AuditRecord(
                user_id,
                result["state"].intent,
                decision.decision,
                decision.reason
            )
        )


        return result
