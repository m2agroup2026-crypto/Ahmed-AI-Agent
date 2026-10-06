from app.api.ai.router import execute_ai
from app.api.ai.schemas import AIRequest
from app.database.connection import SessionLocal
from app.services.current_user_service import get_user_by_id


def test_ai_gateway_request():

    db = SessionLocal()

    try:
        user = get_user_by_id(
            db,
            1
        )

        assert user is not None

        request = AIRequest(
            user_id=user.id,
            command="اعرض المستخدمين"
        )

        response = execute_ai(
            request,
            user,
            db
        )

        assert response.intent is not None

        assert response.decision is not None

        assert response.status is not None

    finally:
        db.close()
