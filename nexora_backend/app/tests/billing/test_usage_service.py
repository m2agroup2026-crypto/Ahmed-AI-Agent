from app.billing.services.usage_service import UsageService


def test_usage_service_creation():

    usage = UsageService().create_usage_record(
        1,
        "AI_REQUEST",
        25
    )

    assert usage["user_id"] == 1

    assert usage["action"] == "AI_REQUEST"

    assert usage["credits"] == 25
