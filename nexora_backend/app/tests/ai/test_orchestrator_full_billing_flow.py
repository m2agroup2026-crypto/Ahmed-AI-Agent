from app.billing.services.billing_context import BillingContext


def test_full_ai_billing_flow():

    context = BillingContext()

    wallet = context.wallet_repository.create_wallet(
        1,
        100
    )

    result = context.process_request(
        1,
        "REPORT_GENERATION"
    )

    assert result["action"] == "REPORT_GENERATION"

    assert result["credits"] == 10

    assert wallet.balance == 90

    assert wallet.total_used == 10
