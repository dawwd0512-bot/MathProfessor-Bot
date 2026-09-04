class ImprovementPlanner:

    def __init__(self):

        self.plans = []


    def create_plan(self, suggestions):

        plan = {
            "steps": []
        }


        for suggestion in suggestions:

            plan["steps"].append(
                {
                    "action": suggestion.get("action"),
                    "target": suggestion.get("target"),
                    "status": "pending"
                }
            )


        self.plans.append(
            plan
        )

        return plan


    def history(self):

        return self.plans
