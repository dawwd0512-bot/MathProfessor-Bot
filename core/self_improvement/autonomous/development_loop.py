from datetime import datetime


class AutonomousDevelopmentLoop:

    def __init__(
        self,
        engine,
        supervisor,
        executor,
        memory
    ):
        self.engine = engine
        self.supervisor = supervisor
        self.executor = executor
        self.memory = memory
        self.history = []


    def evolve(self, goal):

        start = {
            "time": datetime.now().isoformat(),
            "goal": goal
        }


        supervision = self.supervisor.run_cycle(
            goal
        )


        execution = self.executor.execute(
            goal
        )


        result = {
            "start": start,
            "supervision": supervision,
            "execution": execution,
            "success": execution.get(
                "success",
                False
            )
        }


        self.memory.add(
            goal,
            "Autonomous development cycle completed",
            result
        )


        self.history.append(
            result
        )


        return result


    def report(self):

        return {
            "cycles": len(self.history),
            "last": (
                self.history[-1]
                if self.history
                else None
            )
        }
