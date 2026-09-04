from core.self_improvement.analyzer import SelfAnalyzer
from core.self_improvement.optimizer import SelfOptimizer
from core.self_improvement.planner import ImprovementPlanner
from core.self_improvement.validator import ImprovementValidator
from core.self_improvement.tester import SelfTester
from core.self_improvement.memory.improvement_memory import ImprovementMemory


class SelfImprovementEngine:

    def __init__(self):

        self.analyzer = SelfAnalyzer()
        self.optimizer = SelfOptimizer()
        self.planner = ImprovementPlanner()
        self.validator = ImprovementValidator()
        self.tester = SelfTester()
        self.memory = ImprovementMemory()


    def observe(self, event):

        self.analyzer.record(
            event
        )


    def analyze(self):

        return self.analyzer.analyze()


    def suggest(self):

        report = self.analyze()

        return self.optimizer.generate(
            report
        )


    def plan(self):

        suggestions = self.suggest()

        return self.planner.create_plan(
            suggestions
        )


    def validate(self, plan):

        return self.validator.validate(
            plan
        )


    def run_test(self):

        return self.tester.run_tests()


    def improve_cycle(self):

        analysis = self.analyze()

        suggestions = self.optimizer.generate(
            analysis
        )

        plan = self.planner.create_plan(
            suggestions
        )

        valid = self.validator.validate(
            plan
        )

        test = self.tester.run_tests()


        approved = (
            valid
            and test.get(
                "success",
                False
            )
        )


        self.memory.add(
            issue=analysis,
            suggestion=suggestions,
            result={
                "approved": approved,
                "test": test
            }
        )


        return {
            "analysis": analysis,
            "suggestions": suggestions,
            "plan": plan,
            "valid": valid,
            "test": test,
            "approved": approved
        }
