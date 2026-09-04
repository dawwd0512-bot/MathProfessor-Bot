class SelfAnalyzer:

    def __init__(self):
        self.history = []


    def record(self, event):

        self.history.append(
            event
        )


    def analyze(self):

        issues = []

        for event in self.history:

            if isinstance(event, dict):

                if event.get("success") is False:

                    issues.append(
                        {
                            "type": "failure",
                            "message": event.get(
                                "message",
                                "Unknown failure"
                            )
                        }
                    )


        return {
            "events": len(self.history),
            "issues": issues,
            "needs_improvement": len(issues) > 0
        }


    def suggest(self):

        report = self.analyze()

        suggestions = []

        for issue in report["issues"]:

            suggestions.append(
                f"Investigate: {issue['message']}"
            )


        return suggestions
