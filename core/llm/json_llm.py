import json

from core.models import LLM


class JSONLLM:

    def __init__(self):

        self.llm = LLM()

    def ask(self, prompt):

        system = """
أنت محرك قرار.

أعد JSON صالح فقط.

ممنوع كتابة أي مقدمة.
ممنوع كتابة أي شرح.
ممنوع استخدام Markdown.
ممنوع استخدام ```json.

أعد JSON فقط.
"""

        reply = self.llm.ask(
            prompt,
            system=system
        )

        return self.parse(reply)

    def parse(self, text):

        try:

            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1:

                text = text[start:end + 1]

            return json.loads(text)

        except Exception:

            return {
                "success": False,
                "error": "Invalid JSON",
                "raw": text
            }
