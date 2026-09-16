from core.orchestration.agent_registry import AgentRegistry
from core.orchestration.profiles.default_agents import get_default_agents


class AgentManager:
    """
    Manages Ahmed AI specialized agents.
    """

    def __init__(self):
        self.registry = AgentRegistry()


    def load_default_agents(self):

        agents = get_default_agents()

        for agent in agents:
            self.registry.register(agent)


    def list_team(self):

        return self.registry.describe_agents()


    def get_agent(self, name):

        return self.registry.get(name)
