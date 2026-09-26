from app.api.ai.router import execute_ai
from app.api.ai.schemas import AIRequest
from app.database.connection import SessionLocal


def test_ai_gateway_request():

    db = SessionLocal()

    try:
        request = AIRequest(
            user_id=1,
            command="اعرض المستخدمين"
        )

        response = execute_ai(
            request,
            db
        )

        assert response.intent is not None

        assert response.decision is not None

        assert response.status is not None

    finally:
        db.close()
