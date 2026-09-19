from app.ai.command_center.monitoring import MonitoringEngine


def test_monitoring_health():

    health = MonitoringEngine().check(
        "NEXORA_AGENT"
    )

    assert health.component == "NEXORA_AGENT"

    assert health.status == "healthy"
