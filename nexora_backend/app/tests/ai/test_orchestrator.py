from app.database.connection import SessionLocal
from app.ai.core.orchestrator import NexoraOrchestrator


def test_orchestrator_flow():

    db = SessionLocal()

    result = NexoraOrchestrator().run(
        db,
        1,
        "اعرض المستخدمين"
    )

    assert result["state"].intent == "VIEW_USERS"

    assert result["decision"].decision == "ALLOW"

    assert len(result["events"]) > 0

    db.close()
