from app.api.ai.router import execute_ai
from app.api.ai.schemas import AIRequest


def test_ai_gateway_request():

    request = AIRequest(
        user_id=1,
        command="اعرض المستخدمين"
    )

    response = execute_ai(request)

    assert response.status == "received"

    assert response.intent == "PROCESSING"

    assert response.decision == "PENDING"
