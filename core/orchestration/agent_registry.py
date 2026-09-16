from dataclasses import dataclass, field


@dataclass
class AgentProfile:
    """
    Defines an Ahmed AI specialized agent.
    """

    name: str
    role: str
    skills: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    status: str = "available"



class AgentRegistry:
    """
    Central registry for all Ahmed AI agents.
    """


    def __init__(self):
        self.agents = {}


    def register(self, agent: AgentProfile):

        self.agents[agent.name] = agent


    def get(self, name):

        return self.agents.get(name)


    def list_agents(self):

        return list(self.agents.keys())


    def describe_agents(self):

        return [
            {
                "name": agent.name,
                "role": agent.role,
                "skills": agent.skills,
                "tools": agent.tools,
                "status": agent.status
            }
            for agent in self.agents.values()
        ]
