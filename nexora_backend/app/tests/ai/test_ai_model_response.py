from unittest.mock import Mock

from app.api.ai.router import execute_ai
from app.api.ai.schemas import AIRequest


def test_ai_gateway_returns_model_output():
    user = Mock()
    user.id = 1

    request = AIRequest(
        command="Hello NEXORA"
    )

    model_result = {
        "state": Mock(
            intent="GENERAL_QUERY",
            status="approved",
        ),
        "decision": Mock(
            decision="ALLOW",
        ),
        "model_output": "Hello from gpt-5-mini",
    }

    from app.api.ai import router as ai_router

    original_run = ai_router.orchestrator.run

    try:
        ai_router.orchestrator.run = Mock(
            return_value=model_result
        )

        response = execute_ai(
            request,
            user,
            Mock(),
        )
    finally:
        ai_router.orchestrator.run = original_run

    assert response.intent == "GENERAL_QUERY"
    assert response.decision == "ALLOW"
    assert response.status == "approved"
    assert response.model_output == "Hello from gpt-5-mini"
