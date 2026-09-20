from datetime import datetime, UTC


class Wallet:


    def __init__(
        self,
        user_id: int,
        balance: int = 0
    ):

        self.user_id = user_id

        self.balance = balance

        self.total_used = 0

        self.created_at = datetime.now(UTC)

        self.updated_at = datetime.now(UTC)


    def add_credits(
        self,
        amount: int
    ):

        self.balance += amount

        self.updated_at = datetime.now(UTC)


    def consume_credits(
        self,
        amount: int
    ):

        if amount > self.balance:
            raise ValueError(
                "Insufficient credits"
            )

        self.balance -= amount

        self.total_used += amount

        self.updated_at = datetime.now(UTC)
