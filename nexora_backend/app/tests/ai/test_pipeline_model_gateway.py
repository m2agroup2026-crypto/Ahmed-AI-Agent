from unittest.mock import Mock, patch

from app.ai.core.pipeline import AgentPipeline
from app.ai.core.state import AgentState


def test_general_query_calls_model_gateway_once():
    gateway = Mock()
    gateway.generate.return_value = "Hello from NEXORA"

    pipeline = AgentPipeline()
    pipeline.gateway = gateway

    state = AgentState(
        user_id=1,
        input_text="Hello NEXORA",
    )

    with patch(
        "app.ai.core.pipeline.authorize_ai_action",
        return_value={
            "allowed": True,
            "permission": None,
            "reason": "Authenticated intent allowed",
        },
    ):
        result = pipeline.run(
            state,
            db=Mock(),
        )

    gateway.generate.assert_called_once_with(
        "Hello NEXORA"
    )

    assert result["model_output"] == "Hello from NEXORA"


def test_operational_intent_does_not_call_model_gateway():
    gateway = Mock()

    pipeline = AgentPipeline()
    pipeline.gateway = gateway

    state = AgentState(
        user_id=1,
        input_text="اعرض المستخدمين",
    )

    with patch(
        "app.ai.core.pipeline.authorize_ai_action",
        return_value={
            "allowed": True,
            "permission": "users.manage",
            "reason": "Permission validated",
        },
    ):
        pipeline.run(
            state,
            db=Mock(),
        )

    gateway.generate.assert_not_called()


def test_denied_request_does_not_call_model_gateway():
    gateway = Mock()

    pipeline = AgentPipeline()
    pipeline.gateway = gateway

    state = AgentState(
        user_id=1,
        input_text="اعرض المستخدمين",
    )

    with patch(
        "app.ai.core.pipeline.authorize_ai_action",
        return_value={
            "allowed": False,
            "permission": "users.manage",
            "reason": "Permission denied",
        },
    ):
        pipeline.run(
            state,
            db=Mock(),
        )

    gateway.generate.assert_not_called()
