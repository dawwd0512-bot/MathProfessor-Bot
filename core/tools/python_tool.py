from core.tools.base import BaseTool
from core.tools.registry import register


class PythonTool(BaseTool):
    name = "python"

    def execute(self, code):

        try:

            code = code.strip()

            # إذا كان تعبيرًا بسيطًا
            try:

                value = eval(code, {}, {})

                return {
                    "success": True,
                    "tool": self.name,
                    "output": str(value),
                }

            except SyntaxError:
                pass

            namespace = {}

            exec(code, {}, namespace)

            output = namespace.get("output")

            if output is None:
                output = "✅ تم التنفيذ."

            return {
                "success": True,
                "tool": self.name,
                "output": str(output),
            }

        except Exception as e:

            return {
                "success": False,
                "tool": self.name,
                "output": f"❌ خطأ:\n{e}",
            }


register(PythonTool)
