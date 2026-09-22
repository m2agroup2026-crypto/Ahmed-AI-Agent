from app.billing.models.wallet import Wallet
from app.billing.repositories.wallet_repository import WalletRepository


class WalletService:

    def __init__(
        self,
        repository=None,
        db=None
    ):

        self.repository = (
            repository
            or WalletRepository(db=db)
        )

    def create_wallet(
        self,
        user_id: int,
        initial_balance: int = 0
    ):

        wallet = Wallet(
            user_id,
            initial_balance
        )

        return self.repository.create(
            wallet
        )

    def get_wallet(
        self,
        user_id: int
    ):

        return self.repository.get(
            user_id
        )

    def add_credits(
        self,
        user_id: int,
        amount: int
    ):

        wallet = self.get_wallet(
            user_id
        )

        if not wallet:
            wallet = self.create_wallet(
                user_id
            )

        wallet.add_credits(
            amount
        )

        return self.repository.update(
            wallet
        )

    def consume_credits(
        self,
        user_id: int,
        amount: int
    ):

        wallet = self.get_wallet(
            user_id
        )

        if not wallet:
            raise ValueError(
                "Wallet not found"
            )

        wallet.consume_credits(
            amount
        )

        return self.repository.update(
            wallet
        )
