from app.billing.services.credit_service import CreditService


class BillingGuard:


    def __init__(self):

        self.credit_service = CreditService()


    def allow_request(
        self,
        wallet,
        required_credits
    ):

        return self.credit_service.check_user_credits(
            wallet,
            required_credits
        )
