from app.ai.middleware.billing_middleware import BillingMiddleware
from app.billing.services.billing_context import BillingContext


def test_billing_middleware_charge():

    billing = BillingContext()

    billing.create_user_wallet(
        1,
        100
    )

    billing.subscribe_user(
        1,
        1
    )


    middleware = BillingMiddleware()

    middleware.billing.billing = billing


    result = middleware.charge(
        1,
        "REPORT_GENERATION",
        10
    )


    assert result["wallet"].balance == 90

    assert result["transaction"].amount == 10
