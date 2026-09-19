from app.ai.command_center.alerts import AlertEngine


def test_alert_creation():

    alert = AlertEngine().create(
        "INFO",
        "NEXORA AI healthy"
    )

    assert alert.level == "INFO"

    assert alert.message == "NEXORA AI healthy"
