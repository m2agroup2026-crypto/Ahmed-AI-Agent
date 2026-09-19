from app.billing.integration.ai_billing import AIBillingService
from app.billing.models import CreditWallet


def test_ai_billing_process():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    result = AIBillingService().process_ai_request(
        wallet,
        1,
        "AI_REQUEST",
        20
    )

    assert result["user_id"] == 1

    assert result["credits"] == 20

    assert wallet.balance == 80

    assert wallet.total_used == 20
