from app.billing.models import UsageRecord


def test_usage_record_creation():

    usage = UsageRecord(
        user_id=1,
        action="REPORT_GENERATION",
        credits=20
    )

    assert usage.user_id == 1

    assert usage.action == "REPORT_GENERATION"

    assert usage.credits == 20
