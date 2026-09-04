from core.tools.registry.tool_registry import (
    get_tool,
    list_tools,
    execute_tool,
)

import core.tools.file.file_tool
import core.tools.web
import core.tools.terminal.terminal_tool
import core.tools.python_tool
import core.tools.knowledge


class ToolManager:

    def has(self, name):

        return get_tool(name) is not None

    def get(self, name):

        return get_tool(name)

    def execute(self, task):

        if get_tool(task["tool"]) is None:

            return {
                "success": False,
                "tool": task["tool"],
                "error": "Tool not found"
            }

        try:

            output = execute_tool(
                task["tool"],
                task["input"]
            )

            return {
                "success": True,
                "tool": task["tool"],
                "output": output,
            }

        except Exception as e:

            return {
                "success": False,
                "tool": task["tool"],
                "error": str(e)
            }

    def list(self):

        return [
            tool["name"]
            for tool in list_tools()
        ]


    def list_tools(self):
        """Compatibility alias for the tool registry."""
        return self.list()
