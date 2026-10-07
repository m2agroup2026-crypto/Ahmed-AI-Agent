from unittest.mock import Mock

from app.ai.core.orchestrator import NexoraOrchestrator


def test_orchestrator_does_not_charge_after_agent_pipeline():
    orchestrator = NexoraOrchestrator()

    state = Mock()
    state.intent = "GENERAL_QUERY"

    decision = Mock()
    decision.decision = "ALLOW"
    decision.reason = "Authorized"

    agent = Mock()
    agent.process.return_value = {
        "state": state,
        "decision": decision,
        "billing": {"credits": 1},
        "events": [],
    }

    orchestrator.fabric.resolve_agent = Mock(
        return_value=agent
    )

    orchestrator.billing = Mock()
    orchestrator.audit = Mock()

    orchestrator.run(
        db=Mock(),
        user_id=1,
        text="Hello NEXORA",
    )

    orchestrator.billing.charge_ai_action.assert_not_called()
