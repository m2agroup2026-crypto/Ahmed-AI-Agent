from app.ai.core.agent import NexoraAgent
from app.ai.governance.audit import AuditLogger, AuditRecord


class NexoraOrchestrator:


    def __init__(self):

        self.agent = NexoraAgent()

        self.audit = AuditLogger()


    def run(
        self,
        db,
        user_id: int,
        text: str
    ):

        result = self.agent.process(
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
