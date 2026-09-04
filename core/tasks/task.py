class Task:

    def __init__(
        self,
        tool,
        input_data,
        step=None,
        depends_on=None
    ):

        self.tool = tool
        self.input = input_data
        self.step = step
        self.depends_on = depends_on


    def to_dict(self):

        return {
            "step": self.step,
            "tool": self.tool,
            "input": self.input,
            "depends_on": self.depends_on
        }


    def __repr__(self):

        return (
            f"Task("
            f"step={self.step}, "
            f"tool={self.tool}, "
            f"input={self.input}"
            f")"
        )
