from app.billing.services.billing_context import BillingContext
from app.billing.providers.wallet_provider import WalletProvider


class BillingAdapter:


    def __init__(self):

        self.billing = BillingContext()

        self.wallet_provider = WalletProvider()


    def charge_ai_action(
        self,
        user_id,
        action
    ):

        wallet = self.wallet_provider.get_or_create_wallet(
            user_id
        )

        return self.billing.ai_billing.process_ai_request(
            wallet,
            user_id,
            action
        )
