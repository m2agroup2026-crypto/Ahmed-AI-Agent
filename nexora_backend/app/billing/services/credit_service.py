from app.billing.engine.credit_engine import CreditEngine


class CreditService:


    def __init__(self):

        self.engine = CreditEngine()


    def check_user_credits(
        self,
        wallet,
        required_credits
    ):

        return self.engine.check_balance(
            wallet,
            required_credits
        )


    def consume_user_credits(
        self,
        wallet,
        credits
    ):

        return self.engine.consume_credits(
            wallet,
            credits
        )
