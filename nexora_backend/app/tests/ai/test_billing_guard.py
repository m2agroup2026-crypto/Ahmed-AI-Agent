from app.ai.middleware.billing_guard import BillingGuard
from app.billing.models import CreditWallet


def test_billing_guard_allows_request():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    assert BillingGuard().allow_request(
        wallet,
        20
    ) is True


def test_billing_guard_blocks_request():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    assert BillingGuard().allow_request(
        wallet,
        200
    ) is False
