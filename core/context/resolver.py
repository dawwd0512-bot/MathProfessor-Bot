class ContextResolver:

    def resolve(self, message, history):

        if not history:
            return message

        last_user = None

        for item in reversed(history):

            if (
                item["role"] == "user"
                and item["content"] != message
            ):
                last_user = item["content"]
                break

        if last_user is None:
            return message

        pronouns = [
            "سعره",
            "لخصه",
            "اشرحه",
            "اشرح",
            "قارنه",
            "قارن",
        ]

        for word in pronouns:

            if word in message:
                return f"{message} ({last_user})"

        return message
