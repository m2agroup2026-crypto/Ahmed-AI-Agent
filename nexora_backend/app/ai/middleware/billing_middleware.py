from app.ai.integration.billing_adapter_v2 import BillingAdapterV2


class BillingMiddleware:

    def __init__(
        self,
        billing_adapter=None
    ):

        self.billing = (
            billing_adapter
            or BillingAdapterV2()
        )

    def charge(
        self,
        user_id: int,
        action: str,
        credits: int
    ):

        return self.billing.charge_ai_action(
            user_id,
            action,
            credits
        )
