from app.billing.models import CreditWallet


class WalletRepository:


    def __init__(self):

        self.wallets = {}


    def create_wallet(
        self,
        user_id,
        balance=0
    ):

        wallet = CreditWallet(
            user_id,
            balance
        )

        self.wallets[user_id] = wallet

        return wallet


    def get_wallet(
        self,
        user_id
    ):

        return self.wallets.get(
            user_id
        )
