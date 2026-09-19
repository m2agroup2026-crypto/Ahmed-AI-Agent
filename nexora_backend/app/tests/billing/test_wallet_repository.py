from app.billing.repositories.wallet_repository import WalletRepository


def test_wallet_repository_create_and_get():

    repo = WalletRepository()

    wallet = repo.create_wallet(
        1,
        500
    )

    result = repo.get_wallet(1)

    assert result.user_id == 1

    assert result.balance == 500

    assert result.total_used == 0
