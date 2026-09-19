from app.ai.decision.engine import DecisionEngine


def test_decision_allow():

    decision = DecisionEngine().evaluate(
        True,
        "Permission validated"
    )

    assert decision.decision == "ALLOW"

    assert decision.status == "approved"
