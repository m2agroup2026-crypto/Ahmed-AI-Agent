from app.billing.engine.exceptions import InsufficientCreditsError


class CreditEngine:


    def check_balance(
        self,
        wallet,
        required_credits
    ):

        return wallet.balance >= required_credits


    def consume_credits(
        self,
        wallet,
        credits
    ):

        if not self.check_balance(
            wallet,
            credits
        ):
            raise InsufficientCreditsError(
                "Not enough credits"
            )

        wallet.balance -= credits

        wallet.total_used += credits

        return True
