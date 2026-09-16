class ToolManager:
    """
    Controls tool discovery and execution.
    """

    def __init__(self, registry):
        self.registry = registry


    def available_tools(self):
        return self.registry.list_tools()


    def execute(self, tool_name, *args, **kwargs):

        tool = self.registry.get(tool_name)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }


        result = tool(*args, **kwargs)

        return {
            "success": True,
            "result": result
        }
