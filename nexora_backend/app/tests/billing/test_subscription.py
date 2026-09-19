from app.billing.models import Subscription


def test_subscription_creation():

    subscription = Subscription(
        user_id=1,
        plan_id=2
    )

    assert subscription.user_id == 1

    assert subscription.plan_id == 2

    assert subscription.status == "active"
