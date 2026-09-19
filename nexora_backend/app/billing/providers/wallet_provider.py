from app.billing.repositories.wallet_repository import WalletRepository


class WalletProvider:


    def __init__(self):

        self.repository = WalletRepository()


    def get_or_create_wallet(
        self,
        user_id
    ):

        wallet = self.repository.get_wallet(
            user_id
        )


        if wallet is None:

            wallet = self.repository.create_wallet(
                user_id,
                100
            )


        return wallet
