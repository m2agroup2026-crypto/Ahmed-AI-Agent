import pytest

from app.billing.models import CreditWallet
from app.billing.engine.credit_engine import CreditEngine
from app.billing.engine.exceptions import InsufficientCreditsError


def test_consume_credits_success():

    wallet = CreditWallet(
        user_id=1,
        balance=100
    )

    result = CreditEngine().consume_credits(
        wallet,
        20
    )

    assert result is True

    assert wallet.balance == 80

    assert wallet.total_used == 20


def test_consume_credits_failure():

    wallet = CreditWallet(
        user_id=1,
        balance=5
    )

    with pytest.raises(
        InsufficientCreditsError
    ):
        CreditEngine().consume_credits(
            wallet,
            20
        )
