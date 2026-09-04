from core.decision.decision_engine import DecisionEngine


class Planner:

    def __init__(self):
        self.decision = DecisionEngine()

    def create_plan(self, goal):

        text = goal.lower()
        plan = []

        if "search" in text or "internet" in text or "web" in text:
            plan.append({
                "step": 1,
                "tool": "web",
                "input": goal,
            })

            if "save" in text or "file" in text:
                plan.append({
                    "step": 2,
                    "tool": "file",
                    "input": goal,
                })

            plan.append({
                "step": len(plan) + 1,
                "tool": "chat",
                "input": "Summarize the collected information",
            })

            return plan

        tool = self.decision.choose(goal)

        return [
            {
                "step": 1,
                "tool": tool,
                "input": goal,
            }
        ]
