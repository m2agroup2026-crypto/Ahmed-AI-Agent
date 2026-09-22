from app.billing.models.wallet import Wallet


class WalletRepository:

    def __init__(self, db=None):
        self.db = db
        self.wallets = {}

    # ---------------------------------------------------------
    # V2 API
    # ---------------------------------------------------------

    def create(self, wallet):

        if self.db is None:
            self.wallets[wallet.user_id] = wallet
            return wallet

        existing = (
            self.db.query(Wallet)
            .filter(Wallet.user_id == wallet.user_id)
            .first()
        )

        if existing:
            return existing

        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)

        return wallet

    def get(self, user_id: int):

        if self.db is None:
            return self.wallets.get(user_id)

        return (
            self.db.query(Wallet)
            .filter(Wallet.user_id == user_id)
            .first()
        )

    def update(self, wallet):

        if self.db is None:
            self.wallets[wallet.user_id] = wallet
            return wallet

        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)

        return wallet

    # ---------------------------------------------------------
    # Legacy compatibility API
    # ---------------------------------------------------------

    def create_wallet(
        self,
        user_id: int,
        credits: int = 0
    ):

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
