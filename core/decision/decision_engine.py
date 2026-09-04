from core.tools.discovery.discovery import tool_names


class DecisionEngine:

    def choose(self, message):

        text = message.lower()

        if any(word in text for word in [
            "file",
            "pdf",
            "txt",
            "doc",
        ]):
            return "file"

        if any(word in text for word in [
            "terminal",
            "command",
            "bash",
            "shell",
        ]):
            return "terminal"

        if any(word in text for word in [
            "python",
            "code",
            "script",
        ]):
            return "python"

        if any(word in text for word in [
            "web",
            "internet",
            "search",
        ]):
            return "web"

        return "chat"

    def available_tools(self):

        return tool_names()
