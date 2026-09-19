from app.billing.repositories.wallet_repository import WalletRepository
from app.billing.pricing.ai_costs import get_ai_cost
from app.billing.integration.ai_billing import AIBillingService


class BillingContext:


    def __init__(self):

        self.wallet_repository = WalletRepository()

        self.ai_billing = AIBillingService()


    def process_request(
        self,
        user_id,
        action
    ):

        wallet = self.wallet_repository.get_wallet(
            user_id
        )


        if wallet is None:

            wallet = self.wallet_repository.create_wallet(
                user_id,
                0
            )


        return self.ai_billing.process_ai_request(
            wallet,
            user_id,
            action
        )
