class SelfOptimizer:

    def __init__(self):

        self.suggestions = []


    def generate(self, report):

        suggestions = []


        if report.get("needs_improvement"):

            for issue in report.get(
                "issues",
                []
            ):

                message = issue.get(
                    "message",
                    "Unknown issue"
                )

                suggestions.append(
                    {
                        "action": "investigate",
                        "target": message,
                        "priority": "high"
                    }
                )


        else:

            suggestions.append(
                {
                    "action": "optimize",
                    "target": "Improve existing performance",
                    "priority": "low"
                }
            )


        self.suggestions.extend(
            suggestions
        )


        return suggestions


    def history(self):

        return self.suggestions
