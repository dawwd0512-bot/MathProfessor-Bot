from core.goals.goal import Goal


class GoalDecomposer:

    def decompose(self, goal):

        parts = [
            part.strip()
            for part in goal.split("ثم")
            if part.strip()
        ]

        goals = []

        previous = None

        for index, part in enumerate(parts, start=1):

            depends = []

            if previous is not None:
                depends.append(previous)

            goals.append(
                Goal(
                    goal_id=index,
                    text=part,
                    priority=index,
                    depends_on=depends
                )
            )

            previous = index

        return goals
