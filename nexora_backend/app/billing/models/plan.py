from datetime import datetime, UTC


class Plan:


    def __init__(
        self,
        name: str,
        currency: str,
        price: float,
        credits_limit: int,
        billing_cycle: str = "MONTHLY"
    ):

        self.name = name

        self.currency = currency

        self.price = price

        self.credits_limit = credits_limit

        self.billing_cycle = billing_cycle

        self.is_active = True

        self.created_at = datetime.now(UTC)
