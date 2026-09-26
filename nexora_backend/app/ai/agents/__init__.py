from app.ai.agents.registry import AgentRegistry
from app.ai.agents.general import GeneralAgent


registry = AgentRegistry()

registry.register(
    GeneralAgent()
)
