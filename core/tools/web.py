from core.tools.base import BaseTool
from core.tools.registry import register
from core.providers.search import SearchProvider


class WebTool(BaseTool):
    name = "web"

    def __init__(self):
        self.searcher = SearchProvider()

    def execute(self, query):
        result = self.searcher.search(query)

        if not result.get("success"):
            return {
                "success": False,
                "tool": self.name,
                "error": result.get("error", "فشل البحث"),
            }

        return {
            "success": True,
            "tool": self.name,
            "data": result,
        }


register(WebTool)
