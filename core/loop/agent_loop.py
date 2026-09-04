from core.observation.observer import Observer
from core.loop.controller import LoopController
from core.memory.execution_memory import ExecutionMemory
from core.reasoning.reasoner import Reasoner
from core.replanning.replanner import Replanner
from core.goals.decomposer import GoalDecomposer
from core.scheduler.goal_scheduler import GoalScheduler
from core.retry.retry_policy import RetryPolicy
from core.execution.strategy import ExecutionStrategy


class AgentLoop:

    def __init__(self, planner, executor):

        self.planner = planner
        self.executor = executor

        self.observer = Observer()
        self.controller = LoopController()
        self.memory = ExecutionMemory()

        self.reasoner = Reasoner()

        self.replanner = Replanner(
            self.reasoner
        )

        self.decomposer = GoalDecomposer()
        self.scheduler = GoalScheduler()
        self.retry = RetryPolicy()

        self.strategy = ExecutionStrategy(
            self.planner,
            self.executor,
            self.memory,
            self.scheduler,
            self.retry,
        )

        # حماية من حلقات إعادة التخطيط اللانهائية
        self.max_replans = 2


    def run(self, goal, history=None):

        if history is None:
            history = {}

        self.memory.start(goal)

        goals = self.decomposer.decompose(
            goal
        )

        results = []

        replan_count = 0
        replanning_history = []

        while True:

            goal_item = self.scheduler.next_goal(
                goals
            )

            if goal_item is None:
                break

            goal_item.start()

            output = self.strategy.execute_goal(
                goal_item
            )

            if output is None:
                output = []

            results.extend(output)

            report = self.observer.observe(
                output
            )

            success = (
                len(output) > 0
                and all(
                    item.get(
                        "success",
                        False
                    )
                    for item in output
                    if isinstance(item, dict)
                )
            )

            # ==================================================
            # SUCCESS
            # ==================================================

            if success:
                continue

            # ==================================================
            # FAILURE
            # ==================================================

            # إذا بقيت المهمة pending فهذا يعني أن RetryPolicy
            # أعاد ضبطها للمحاولة مرة أخرى.
            if goal_item.status == goal_item.PENDING:

                continue

            # ==================================================
            # REPLANNING
            # ==================================================

            if replan_count >= self.max_replans:

                self.scheduler.block_dependents(
                    goals
                )

                break

            replan_count += 1

            analysis = self.reasoner.analyze(
                goal_item.text,
                report,
                self.memory.history()
            )

            replanning = self.replanner.replan(
                goal_item.text,
                report,
                self.memory.history()
            )

            replanning_history.append(
                {
                    "attempt": replan_count,
                    "goal": goal_item.text,
                    "analysis": analysis,
                    "next_goal": replanning.get(
                        "next_goal",
                        ""
                    ),
                }
            )

            next_goal_text = replanning.get(
                "next_goal"
            )

            if not next_goal_text:

                self.scheduler.block_dependents(
                    goals
                )

                break

            # ==================================================
            # تنفيذ الخطة الجديدة فعليًا
            # ==================================================

            new_goals = self.decomposer.decompose(
                next_goal_text
            )

            # نبدأ من جديد بالخطة الجديدة مع الحفاظ
            # على ذاكرة التنفيذ السابقة.
            goals = new_goals

            self.scheduler = GoalScheduler()

            # إعادة ربط الاستراتيجية بالـscheduler الجديد
            self.strategy.scheduler = self.scheduler

            continue

        final_report = self.observer.observe(
            results
        )

        continue_loop = self.controller.should_continue(
            final_report
        )

        return {
            "results": results,
            "report": final_report,
            "memory": self.memory.history(),
            "continue": continue_loop,
            "replanning": (
                replanning_history
                if replanning_history
                else None
            ),
            "replans": replan_count,
            "goals": self.scheduler.summary(
                goals
            ),
        }
