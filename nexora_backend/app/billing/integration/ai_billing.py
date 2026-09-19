from app.billing.services.credit_service import CreditService
from app.billing.services.usage_service import UsageService
from app.billing.pricing.ai_costs import get_ai_cost


class AIBillingService:


    def __init__(self):

        self.credit_service = CreditService()

        self.usage_service = UsageService()


    def process_ai_request(
        self,
        wallet,
        user_id,
        action,
        credits=None
    ):

        if credits is None:
            credits = get_ai_cost(action)


        self.credit_service.consume_user_credits(
            wallet,
            credits
        )


        usage = self.usage_service.create_usage_record(
            user_id,
            action,
            credits
        )


        return usage
