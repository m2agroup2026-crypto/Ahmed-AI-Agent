from app.ai.integration.billing_adapter import BillingAdapter


def test_billing_adapter():

    adapter = BillingAdapter()

    result = adapter.charge_ai_action(
        1,
        "GENERAL_QUERY"
    )

    assert result["user_id"] == 1

    assert result["action"] == "GENERAL_QUERY"

    assert result["credits"] == 1
