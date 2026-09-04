from core.executor.task_executor import TaskExecutor
from core.memory.execution_memory import ExecutionMemory


class PlanExecutor:

    def __init__(self):

        self.executor = TaskExecutor()
        self.memory = ExecutionMemory()


    def execute(self, plan):

        results = []

        self.memory.start(plan)


        for step in plan:

            task_input = step["input"]

            dependency = step.get(
                "depends_on"
            )


            context = None


            if dependency is not None:

                for item in self.memory.steps:

                    if item["step"] == dependency:

                        context = item["result"]

                        break


            if context is not None:

                if isinstance(task_input, str):

                    task_input = (
                        f"{task_input}\n\n"
                        f"نتيجة الخطوة السابقة:\n{context}\n\n"
                        "استخدم هذه النتيجة مباشرة وأكمل المهمة بناءً عليها."
                    )

                elif isinstance(task_input, dict):

                    task_input["context"] = context


            task = {
                "tool": step["tool"],
                "input": task_input,
            }


            output = self.executor.execute(
                [task]
            )


            self.memory.add_step(
                step["step"],
                output
            )


            results.append(
                {
                    "step": step["step"],
                    "tool": step["tool"],
                    "result": output,
                }
            )


        return results
