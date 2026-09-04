from core.tasks.task import Task
from core.planning.analyzer import TaskAnalyzer


class PlannerV2:

    def __init__(self):

        self.analyzer = TaskAnalyzer()


    def plan(self, message, history=None):

        if history is None:
            history = {}


        tasks = []


        parts = [
            part.strip()
            for part in message.split("ثم")
            if part.strip()
        ]


        previous_step = None


        for index, part in enumerate(parts, start=1):

            analysis = self.analyzer.analyze(
                part
            )

            tool = analysis.get(
                "tool",
                "chat"
            )


            task_input = part


            if tool == "terminal":

                command = part.lower()


                if (
                    "اعرض ملفات" in command
                    or "ملفات المشروع" in command
                ):
                    command = "ls"

                elif (
                    "حالة المشروع" in command
                    or "حالة git" in command
                ):
                    command = "git status"

                elif "المسار" in command:
                    command = "pwd"


                task_input = command


            elif tool in ("python", "math"):

                task_input = part.replace(
                    "احسب",
                    "",
                    1
                ).strip()


                task_input = task_input.replace(
                    "اضرب",
                    ""
                )

                task_input = task_input.replace(
                    "في",
                    "*"
                )

                task_input = task_input.replace(
                    "اقسم",
                    ""
                )

                task_input = task_input.replace(
                    "على",
                    "/"
                )

                task_input = task_input.replace(
                    "اجمع",
                    "+"
                )

                task_input = task_input.replace(
                    "اطرح",
                    "-"
                )

                task_input = task_input.strip()



            previous = None


            if (
                history
                and isinstance(history, dict)
                and history.get("steps")
            ):

                for step in reversed(history["steps"]):

                    result = step.get(
                        "result"
                    )


                    if not isinstance(
                        result,
                        list
                    ):
                        continue


                    for item in result:

                        if (
                            isinstance(item, dict)
                            and item.get("tool") in ("python", "math")
                        ):

                            output = item.get(
                                "output"
                            )


                            if (
                                isinstance(output, dict)
                                and "output" in output
                            ):

                                previous = output["output"]

                            else:

                                previous = output


                            break


                    if previous is not None:
                        break



            if previous is not None:

                previous = str(
                    previous
                ).strip()


                if tool == "chat":

                    if any(
                        word in part
                        for word in [
                            "اشرح",
                            "حلل",
                            "لخص",
                            "اكتب",
                            "استخدم",
                            "الناتج",
                            "النتيجة"
                        ]
                    ):

                        task_input = (
                            f"{part}\n\n"
                            f"نتيجة الخطوة السابقة:\n"
                            f"{previous}\n\n"
                            "استخدم هذه النتيجة مباشرة."
                        )


                elif tool in ("python", "math"):

                    task_input = task_input.replace(
                        "الناتج",
                        previous
                    )

                    task_input = task_input.replace(
                        "النتيجة",
                        previous
                    )



            task = Task(
                tool,
                task_input,
                step=index,
                depends_on=previous_step
            )


            tasks.append(
                task
            )


            previous_step = index


        return tasks
