from app.billing.models import CreditWallet
from app.billing.integration.ai_billing import AIBillingService


def test_orchestrator_billing_flow():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    result = AIBillingService().process_ai_request(
        wallet,
        1,
        "AI_REQUEST",
        10
    )

    assert result["credits"] == 10

    assert wallet.balance == 90
