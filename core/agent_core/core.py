from core.loop.agent_loop import AgentLoop
from core.executor.task_executor import TaskExecutor


class AgentCore:

    def __init__(self, llm, memory, planner, tools, loop=None):
        self.llm = llm
        self.memory = memory
        self.planner = planner
        self.tools = tools

        # استخدم AgentLoop الحقيقي الموجود في المشروع.
        # لا نعيد بناء مسار الرياضيات.
        self.loop = loop or AgentLoop(
            self.planner,
            TaskExecutor()
        )

    def remember(self, user_id, key, value):
        self.memory.set(user_id, key, value)

    def recall(self, user_id, key, default=None):
        return self.memory.get(user_id, key, default)

    def remember_conversation(self, user_id, role, content):
        if hasattr(self.memory, "add_message"):
            self.memory.add_message(user_id, role, content)

    def conversation(self, user_id, limit=20):
        if hasattr(self.memory, "get_history"):
            return self.memory.get_history(user_id, limit)
        return []

    def plan(self, message, history=None):
        return self.planner.plan(message, history)

    def chat(self, message, history=None):
        if self.llm is None or not hasattr(self.llm, "ask"):
            return None

        try:
            return self.llm.ask(message)
        except Exception:
            return None

    def decompose(self, message):
        return self.plan(message)

    def available_tools(self):
        try:
            return self.tools.list_tools()
        except Exception:
            return []

    def execute_tool(self, tool, data):
        try:
            from core.tools.registry.tool_registry import execute_tool
            return execute_tool(tool, data)
        except Exception as e:
            return {
                "success": False,
                "tool": tool,
                "output": f"Tool Error: {type(e).__name__}: {e}"
            }

    def reflect(self, result):
        if isinstance(result, dict):
            success = result.get("success", False)
            return {
                "success": bool(success),
                "needs_retry": not bool(success),
                "result": result
            }

        return {
            "success": bool(result),
            "needs_retry": not bool(result),
            "result": result
        }

    def decide(self, message, reflection=None):
        reflection = reflection or {}

        if reflection.get("needs_retry"):
            return "retry"

        if isinstance(message, str):
            if message.strip().startswith("/"):
                return "tool"

        return "chat"

    def run(self, message, user_id=None, history=None):
        if history is None:
            history = {}

        # AgentCore يستخدم الـ AgentLoop الحقيقي.
        # AgentLoop بدوره يستخدم PlannerV2 + TaskExecutor.
        result = self.loop.run(
            message,
            history
        )

        return result
