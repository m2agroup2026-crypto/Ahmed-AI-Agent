from app.billing.services.billing_context import BillingContext


def test_billing_context_flow():

    context = BillingContext()

    context.wallet_repository.create_wallet(
        1,
        100
    )

    result = context.process_request(
        1,
        "GENERAL_QUERY"
    )

    assert result["user_id"] == 1

    assert result["action"] == "GENERAL_QUERY"

    assert result["credits"] == 1
