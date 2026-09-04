class ImprovementValidator:

    def __init__(self):

        self.allowed_actions = [
            "investigate",
            "optimize",
            "test"
        ]


    def validate(self, plan):

        if not plan:
            return False


        for step in plan.get(
            "steps",
            []
        ):

            action = step.get(
                "action"
            )

            if action not in self.allowed_actions:
                return False


        return True
