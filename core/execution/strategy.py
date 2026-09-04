class ExecutionStrategy:

    def __init__(
        self,
        planner,
        executor,
        memory,
        scheduler,
        retry,
    ):

        self.planner = planner
        self.executor = executor

        self.memory = memory

        self.scheduler = scheduler
        self.retry = retry


    def execute_goal(self, goal_item):

        history = self.memory.history()


        tasks = self.planner.plan(
            goal_item.text,
            history,
        )


        output = self.executor.execute(
            tasks
        )


        if output is None:
            output = []


        self.memory.add_step(
            goal_item,
            output
        )


        success = (
            len(output) > 0
            and all(
                item.get(
                    "success",
                    False,
                )
                for item in output
            )
        )


        if success:

            self.scheduler.complete(
                goal_item,
                output,
            )

        else:

            retry = self.retry.on_failure(
                goal_item
            )

            if retry:
                return output

            self.scheduler.fail(
                goal_item,
                output,
            )


        return output
