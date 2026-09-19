from app.billing.models import CreditWallet


def test_credit_wallet_creation():

    wallet = CreditWallet(
        user_id=1,
        balance=5000
    )

    assert wallet.user_id == 1

    assert wallet.balance == 5000

    assert wallet.total_used == 0
