from app.billing.services.billing_context import BillingContext


def test_persistent_billing_flow():

    billing = BillingContext()

    billing.create_user_wallet(
        1,
        100
    )

    billing.subscribe_user(
        1,
        1
    )


    result = billing.process_ai_request(
        1,
        "REPORT_GENERATION",
        10
    )


    assert result["wallet"].balance == 90

    assert result["wallet"].total_used == 10

    assert result["transaction"].amount == 10

    assert result["transaction"].balance_before == 100

    assert result["transaction"].balance_after == 90
