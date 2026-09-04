class LoopController:

    def should_continue(self, report):

        if not report:
            return False

        for item in report:

            if not item["success"]:
                return True

        return False
