class GoalScheduler:

    def __init__(self):

        self.completed = set()

        self.failed = set()


    def next_goal(self, goals):

        candidates = sorted(
            goals,
            key=lambda g: g.priority
        )

        for goal in candidates:

            if goal.status != goal.PENDING:
                continue

            if goal.is_ready(self.completed):

                return goal

        return None


    def complete(self, goal, result=None):

        goal.complete(result)

        self.completed.add(goal.id)


    def fail(self, goal, error=None):

        goal.fail(error)

        self.failed.add(goal.id)


    def block_dependents(self, goals):

        for goal in goals:

            if goal.status != goal.PENDING:
                continue

            for dep in goal.depends_on:

                if dep in self.failed:

                    goal.block()

                    break


    def has_pending(self, goals):

        for goal in goals:

            if goal.status == goal.PENDING:

                return True

        return False


    def summary(self, goals):

        return [
            goal.to_dict()
            for goal in goals
        ]

