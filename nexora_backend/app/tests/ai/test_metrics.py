from app.ai.command_center.metrics import MetricsCollector


def test_metrics_collection():

    metrics = MetricsCollector().collect([])

    assert metrics.total_requests == 0

    assert metrics.approved_actions == 0

    assert metrics.system_status == "healthy"
