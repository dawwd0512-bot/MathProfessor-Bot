class Goal:

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


    def __init__(
        self,
        goal_id,
        text,
        priority=1,
        depends_on=None,
    ):

        self.id = goal_id
        self.text = text

        self.priority = priority

        self.depends_on = depends_on or []

        self.status = Goal.PENDING

        self.result = None

        self.error = None

        self.retry_count = 0


    def is_ready(self, completed):

        for dep in self.depends_on:

            if dep not in completed:

                return False

        return True


    def start(self):

        self.status = Goal.RUNNING


    def complete(self, result=None):

        self.status = Goal.COMPLETED
        self.result = result


    def fail(self, error=None):

        self.status = Goal.FAILED
        self.error = error
        self.retry_count += 1


    def block(self):

        self.status = Goal.BLOCKED


    def reset(self):

        self.status = Goal.PENDING
        self.result = None
        self.error = None


    def to_dict(self):

        return {
            "id": self.id,
            "text": self.text,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "status": self.status,
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error,
        }


    def __repr__(self):

        return (
            f"Goal("
            f"id={self.id}, "
            f"status={self.status}, "
            f"text={self.text}"
            f")"
        )
