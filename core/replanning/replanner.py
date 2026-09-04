class Replanner:

    def __init__(self, reasoner):

        self.reasoner = reasoner


    def replan(self, goal, report, memory):

        analysis = self.reasoner.analyze(
            goal,
            report,
            memory
        )

        next_goal = (
            f"""
المهمة الأصلية:
{goal}

حدث فشل في المحاولة السابقة.

تحليل السبب:
{analysis}

أنشئ طريقة جديدة لتحقيق الهدف.
"""
        )

        return {
            "analysis": analysis,
            "next_goal": next_goal
        }
