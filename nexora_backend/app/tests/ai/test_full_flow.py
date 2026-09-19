from app.ai.core.agent import NexoraAgent
from app.ai.core.fabric import IntelligenceFabric


def test_ai_full_flow():

    assert NexoraAgent() is not None

    assert IntelligenceFabric() is not None
