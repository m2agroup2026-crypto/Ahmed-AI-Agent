from app.billing.pricing.ai_costs import get_ai_cost


def test_ai_pricing():

    assert get_ai_cost(
        "REPORT_GENERATION"
    ) == 10


    assert get_ai_cost(
        "GENERAL_QUERY"
    ) == 1


    assert get_ai_cost(
        "UNKNOWN_ACTION"
    ) == 1
