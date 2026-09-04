import core.tools.file.file_tool
import core.tools.terminal.terminal_tool
import core.tools.python_tool
import core.tools.web
import core.tools.knowledge

from core.tools.registry.tool_registry import list_tools


def discover_tools():

    return list_tools()


def tool_names():

    return [
        tool["name"]
        for tool in list_tools()
    ]
