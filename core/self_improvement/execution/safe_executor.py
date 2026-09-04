import os
import shutil
from datetime import datetime

from core.self_improvement.code_modifier.code_modifier import CodeModifier


class SafeExecutor:

    def __init__(self):

        self.records = []

        self.modifier = CodeModifier()


    def backup(self, path):

        if not os.path.exists(path):
            return None

        backup_path = (
            f"{path}.backup."
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        shutil.copy2(
            path,
            backup_path
        )

        return backup_path


    def execute(self, action, **kwargs):

        result = {
            "action": action,
            "success": False,
            "status": "pending",
            "time": datetime.now().isoformat()
        }

        try:

            if action == "modify_file":

                file_path = kwargs.get("file")

                content = kwargs.get("content")

                modify_result = self.modifier.modify(
                    file_path,
                    content
                )

                self.records.append(
                    modify_result
                )

                return modify_result


            if not action:

                result["status"] = "empty"

            else:

                result["success"] = True

                result["status"] = "validated"

        except Exception as e:

            result["error"] = str(e)

        self.records.append(
            result
        )

        return result


    def history(self):

        return self.records
