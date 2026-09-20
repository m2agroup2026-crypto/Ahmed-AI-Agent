from app.billing.services.wallet_service import WalletService
from app.billing.services.subscription_service import SubscriptionService
from app.billing.services.credit_ledger_service import CreditLedgerService
from app.billing.integration.ai_billing import AIBillingService


class BillingContext:

    def __init__(
        self,
        wallet_service=None,
        subscription_service=None
    ):

        self.wallet_service = (
            wallet_service
            or WalletService()
        )

        self.subscription_service = (
            subscription_service
            or SubscriptionService()
        )

        # Legacy compatibility
        self.wallet_repository = self.wallet_service.repository

        self.subscription_repository = (
            self.subscription_service.repository
        )

        self.ai_billing = AIBillingService()

        # V2 billing
        self.ledger_service = CreditLedgerService(
            self.wallet_service
        )

    # ---------------------------------------------------------
    # Legacy API
    # ---------------------------------------------------------

    def process_request(
        self,
        user_id: int,
        action: str
    ):

        wallet = self.wallet_repository.get_wallet(
            user_id
        )

        if not wallet:
            wallet = self.wallet_repository.create_wallet(
                user_id,
                0
            )

        return self.ai_billing.process_ai_request(
            wallet,
            user_id,
            action
        )

    # ---------------------------------------------------------
    # V2 API
    # ---------------------------------------------------------

    def create_user_wallet(
        self,
        user_id: int,
        credits: int = 0
    ):

        return self.wallet_service.create_wallet(
            user_id,
            credits
        )

    def subscribe_user(
        self,
        user_id: int,
        plan_id: int
    ):

        return self.subscription_service.create_subscription(
            user_id,
            plan_id
        )

    def process_ai_request(
        self,
        user_id: int,
        action: str,
        credits: int
    ):

        subscription = self.subscription_service.get_subscription(
            user_id
        )

        if not subscription:

            raise ValueError(
                "No active subscription"
            )

        return self.ledger_service.consume(
            user_id,
            action,
            credits
        )
