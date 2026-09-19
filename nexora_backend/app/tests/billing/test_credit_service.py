from app.billing.models import CreditWallet
from app.billing.services.credit_service import CreditService


def test_credit_service_consumption():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    service = CreditService()

    result = service.consume_user_credits(
        wallet,
        25
    )

    assert result is True

    assert wallet.balance == 75

    assert wallet.total_used == 25
