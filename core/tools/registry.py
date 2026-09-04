TOOLS = {}


def register(tool_class):
    instance = tool_class()
    TOOLS[instance.name] = instance


def get(name):
    return TOOLS.get(name)


def all_tools():
    return TOOLS
