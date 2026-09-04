class BaseTool:
    name = "tool"

    def execute(self, data):
        raise NotImplementedError(
            "Tool must implement execute()"
        ) 
