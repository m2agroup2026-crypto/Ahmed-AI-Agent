from app.billing.models import Plan


def test_plan_creation():

    plan = Plan(
        "Professional",
        "EGP",
        799,
        50000
    )

    assert plan.name == "Professional"

    assert plan.currency == "EGP"

    assert plan.price == 799

    assert plan.credits_limit == 50000
