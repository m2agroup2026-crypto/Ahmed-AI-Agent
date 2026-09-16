from dataclasses import dataclass


@dataclass
class ToolDefinition:
    name: str
    category: str
    description: str
    risk_level: str = "low"
    requires_approval: bool = False
    handler: object = None



class ToolRegistry:
    """
    Central registry for Ahmed AI tools.
    """

    def __init__(self):
        self.tools = {}


    def register(self, tool: ToolDefinition):
        self.tools[tool.name] = tool


    def get(self, name):
        return self.tools.get(name)


    def list_tools(self):
        return list(self.tools.keys())


    def describe_tools(self):
        return [
            {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "risk_level": tool.risk_level,
                "requires_approval": tool.requires_approval
            }
            for tool in self.tools.values()
        ]
