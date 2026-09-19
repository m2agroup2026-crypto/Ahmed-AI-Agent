from app.billing.integration.ai_billing import AIBillingService
from app.billing.models import CreditWallet


def test_ai_billing_dynamic_pricing():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    result = AIBillingService().process_ai_request(
        wallet,
        1,
        "REPORT_GENERATION"
    )

    assert result["credits"] == 10

    assert wallet.balance == 90

    assert wallet.total_used == 10
