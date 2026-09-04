class Mission:

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


    def __init__(self, mission_id, goal, goals):

        self.id = mission_id

        self.goal = goal

        self.goals = goals

        self.status = Mission.PENDING

        self.progress = 0.0

        self.result = None

        self.error = None



    def start(self):

        self.status = Mission.RUNNING



    def complete(self, result=None):

        self.status = Mission.COMPLETED

        self.progress = 100.0

        self.result = self.make_serializable(
            result
        )



    def fail(self, error=None):

        self.status = Mission.FAILED

        self.error = str(error)



    def update_progress(self):

        if not self.goals:

            self.progress = 100.0

            return


        completed = sum(
            1
            for goal in self.goals
            if goal.status == goal.COMPLETED
        )


        self.progress = (
            completed / len(self.goals)
        ) * 100



    def make_serializable(self, obj):

        if obj is None:

            return None


        if isinstance(obj, (str, int, float, bool)):

            return obj


        if isinstance(obj, list):

            return [
                self.make_serializable(
                    item
                )
                for item in obj
            ]


        if isinstance(obj, dict):

            return {
                str(key): self.make_serializable(value)
                for key, value in obj.items()
            }


        if hasattr(obj, "to_dict"):

            return self.make_serializable(
                obj.to_dict()
            )


        return str(obj)



    def to_dict(self):

        return {

            "id": self.id,

            "goal": self.goal,

            "status": self.status,

            "progress": self.progress,

            "result": self.result,

            "error": self.error,

            "goals": [
                self.make_serializable(goal)
                for goal in self.goals
            ]
        }



    def __repr__(self):

        return (
            f"Mission("
            f"id={self.id}, "
            f"status={self.status}, "
            f"progress={self.progress:.1f}%"
            f")"
        )
