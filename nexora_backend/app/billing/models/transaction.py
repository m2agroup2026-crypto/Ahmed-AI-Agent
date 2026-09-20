from datetime import datetime, UTC


class CreditTransaction:


    def __init__(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        balance_before: int,
        balance_after: int,
        reference: str = None
    ):

        self.user_id = user_id

        self.transaction_type = transaction_type

        self.amount = amount

        self.balance_before = balance_before

        self.balance_after = balance_after

        self.reference = reference

        self.created_at = datetime.now(UTC)
