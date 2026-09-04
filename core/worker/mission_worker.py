from core.loop.agent_loop import AgentLoop
from core.planner_v2 import PlannerV2
from core.executor.task_executor import TaskExecutor


class MissionWorker:

    def __init__(self, mission_manager):

        self.manager = mission_manager

        self.planner = PlannerV2()

        self.executor = TaskExecutor()

        self.loop = AgentLoop(
            self.planner,
            self.executor
        )


    def run_once(self):

        mission = self.manager.next()


        if mission is None:

            return None


        self.manager.start(
            mission
        )


        try:

            result = self.loop.run(
                mission.goal,
                []
            )


            output = result.get(
                "results",
                []
            )


            success = (
                len(output) > 0
                and all(
                    item.get(
                        "success",
                        False
                    )
                    for item in output
                )
            )


            if success:

                self.manager.complete(
                    mission,
                    result
                )

            else:

                self.manager.complete(
                    mission,
                    result
                )


            return mission



        except Exception as e:


            print(
                "WORKER ERROR:",
                e
            )


            self.manager.fail(
                mission,
                str(e)
            )


            return mission
