from .tool_registry import (
    register_tool,
    get_tool,
    list_tools,
    execute_tool,
)

TOOLS = {}


def register(tool_class):

    tool = tool_class()

    TOOLS[tool.name] = tool

    register_tool(
        tool.name,
        getattr(tool, "description", ""),
        tool.execute,
    )


def get(name):

    return TOOLS.get(name)


def all_tools():

    return TOOLS
