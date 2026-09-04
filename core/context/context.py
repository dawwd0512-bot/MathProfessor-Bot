class Context:

    def __init__(self):
        self.history = []

    def add(self, role, content):
        self.history.append(
            {
                "role": role,
                "content": content,
            }
        )

    def last(self):

        if not self.history:
            return None

        return self.history[-1]

    def all(self):
        return self.history

    def clear(self):
        self.history.clear()
