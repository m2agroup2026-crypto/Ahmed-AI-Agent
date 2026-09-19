from app.database.connection import SessionLocal
from app.ai.core.state import AgentState
from app.ai.core.pipeline import AgentPipeline


def test_pipeline_detects_intent():

    db = SessionLocal()

    state = AgentState(
        1,
        "اعرض المستخدمين"
    )

    result = AgentPipeline().run(
        state,
        db
    )

    assert result["state"].intent == "VIEW_USERS"

    assert result["state"].permission == "users.manage"

    db.close()
