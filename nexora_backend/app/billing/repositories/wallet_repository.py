class WalletRepository:

    def __init__(self):
        self.wallets = {}

    # V2 API
    def create(
        self,
        wallet
    ):
        self.wallets[wallet.user_id] = wallet
        return wallet

    def get(
        self,
        user_id: int
    ):
        return self.wallets.get(user_id)

    def update(
        self,
        wallet
    ):
        self.wallets[wallet.user_id] = wallet
        return wallet

    # Legacy compatibility API
    def create_wallet(
        self,
        user_id: int,
        credits: int = 0
    ):
        from app.billing.models.wallet import Wallet

        wallet = Wallet(
            user_id,
            credits
        )

        return self.create(wallet)

    def get_wallet(
        self,
        user_id: int
    ):
        return self.get(user_id)
