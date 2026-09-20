from app.billing.services.billing_context import BillingContext


class BillingAdapterV2:


    def __init__(
        self,
        billing_context=None
    ):

        self.billing = (
            billing_context
            or BillingContext()
        )



    def charge_ai_action(
        self,
        user_id: int,
        action: str,
        credits: int
    ):

        return self.billing.process_ai_request(
            user_id,
            action,
            credits
        )
