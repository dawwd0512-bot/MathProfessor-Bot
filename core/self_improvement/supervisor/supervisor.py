from datetime import datetime


class ImprovementSupervisor:

    def __init__(self, engine):

        self.engine = engine
        self.cycles = []


    def run_cycle(self, goal):

        start = {
            "time": datetime.now().isoformat(),
            "goal": goal
        }


        self.engine.observe(
            {
                "success": True,
                "message": f"Supervisor started: {goal}"
            }
        )


        result = self.engine.improve_cycle()


        cycle = {
            "start": start,
            "result": result
        }


        self.cycles.append(
            cycle
        )


        return cycle



    def history(self):

        return self.cycles



    def status(self):

        return {
            "cycles": len(self.cycles),
            "last": self.cycles[-1]
            if self.cycles
            else None
        }
