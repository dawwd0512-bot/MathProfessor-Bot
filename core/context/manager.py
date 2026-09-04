from core.context.context import Context


class ContextManager:

    def __init__(self):
        self.context = Context()

    def add_user(self, message):
        self.context.add("user", message)

    def add_assistant(self, message):
        self.context.add("assistant", message)

    def last(self):
        return self.context.last()

    def history(self):
        return self.context.all()

    def clear(self):
        self.context.clear()
