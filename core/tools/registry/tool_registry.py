TOOLS = {}


def register_tool(name, description, func):

    TOOLS[name] = {
        "description": description,
        "function": func,
    }


def get_tool(name):

    return TOOLS.get(name)


def list_tools():

    return [
        {
            "name": name,
            "description": tool["description"],
        }
        for name, tool in TOOLS.items()
    ]


def execute_tool(name, *args, **kwargs):

    tool = get_tool(name)

    if tool is None:
        raise ValueError(
            f"Tool '{name}' not found."
        )

    return tool["function"](
        *args,
        **kwargs
    )
