from app.billing.models.transaction import CreditTransaction
from app.billing.models.usage import UsageRecord
from app.billing.repositories.transaction_repository import TransactionRepository
from app.billing.repositories.usage_repository import UsageRepository


class CreditLedgerService:


    def __init__(
        self,
        wallet_service
    ):

        self.wallet_service = wallet_service

        self.transaction_repository = TransactionRepository()

        self.usage_repository = UsageRepository()



    def consume(
        self,
        user_id: int,
        action: str,
        credits: int
    ):

        wallet = self.wallet_service.get_wallet(
            user_id
        )

        if not wallet:
            raise ValueError(
                "Wallet not found"
            )


        balance_before = wallet.balance


        self.wallet_service.consume_credits(
            user_id,
            credits
        )


        balance_after = wallet.balance


        transaction = CreditTransaction(
            user_id,
            "AI_USAGE",
            credits,
            balance_before,
            balance_after,
            action
        )


        usage = UsageRecord(
            user_id,
            action,
            credits
        )


        self.transaction_repository.create(
            transaction
        )


        self.usage_repository.create(
            usage
        )


        return {
            "transaction": transaction,
            "usage": usage,
            "wallet": wallet
        }
