from tools.core.tool_permission import ToolPermissionGateway


class ToolExecutor:
    """
    Central execution gateway for Ahmed AI tools.

    Responsibilities:
    - Resolve tools from the registry
    - Enforce permission checks
    - Validate tool handlers
    - Execute approved tools
    - Return structured results
    - Prevent tool exceptions from crashing the runtime
    """

    def __init__(self, registry, permission_gateway=None):
        self.registry = registry
        self.permission_gateway = (
            permission_gateway or ToolPermissionGateway()
        )


    def execute(self, tool_name, *args, **kwargs):

        tool = self.registry.get(tool_name)

        if tool is None:
            return {
                "success": False,
                "tool": tool_name,
                "status": "not_found",
                "error": f"Tool '{tool_name}' was not found"
            }


        # Support both ToolDefinition objects and dictionary definitions.
        if isinstance(tool, dict):
            definition = tool
            handler = tool.get("handler")
        else:
            definition = {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "risk_level": tool.risk_level,
                "requires_approval": tool.requires_approval
            }

            handler = tool.handler


        permission = self.permission_gateway.check(definition)

        if not permission.get("allowed", False):
            return {
                "success": False,
                "tool": tool_name,
                "status": "approval_required",
                "error": permission.get(
                    "reason",
                    "Tool execution was not permitted"
                )
            }


        if not callable(handler):
            return {
                "success": False,
                "tool": tool_name,
                "status": "invalid_handler",
                "error": "Tool handler is not callable"
            }


        try:
            result = handler(*args, **kwargs)

            return {
                "success": True,
                "tool": tool_name,
                "status": "completed",
                "result": result
            }

        except Exception as exc:
            return {
                "success": False,
                "tool": tool_name,
                "status": "execution_error",
                "error": str(exc)
            }
