import os

from core.tools.base import BaseTool
from core.tools.registry import register


class FileTool(BaseTool):

    name = "file"


    def execute(self, data):

        try:

            action = data.get(
                "action",
                "read"
            )

            path = data.get(
                "path"
            )


            if not path:
                return {
                    "success": False,
                    "tool": self.name,
                    "error": "Missing file path"
                }


            if action == "read":

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    content = f.read()


                return {
                    "success": True,
                    "tool": self.name,
                    "output": content
                }


            if action == "write":

                content = data.get(
                    "content",
                    ""
                )

                with open(
                    path,
                    "w",
                    encoding="utf-8"
                ) as f:

                    f.write(content)


                return {
                    "success": True,
                    "tool": self.name,
                    "output": "File written"
                }


            if action == "exists":

                return {
                    "success": True,
                    "tool": self.name,
                    "output": os.path.exists(path)
                }


            return {
                "success": False,
                "tool": self.name,
                "error": "Unknown action"
            }


        except Exception as e:

            return {
                "success": False,
                "tool": self.name,
                "error": str(e)
            }


register(FileTool)
