from pathlib import Path
from datetime import datetime
import shutil
import py_compile


class CodeModifier:

    def __init__(self):

        self.history = []

    def modify(self, file_path, new_content):

        file_path = Path(file_path)

        if not file_path.exists():

            return {
                "success": False,
                "error": "File not found"
            }

        backup = file_path.with_suffix(
            file_path.suffix + ".bak"
        )

        shutil.copy2(
            file_path,
            backup
        )

        try:

            file_path.write_text(
                new_content,
                encoding="utf-8"
            )

            py_compile.compile(
                str(file_path),
                doraise=True
            )

            report = {
                "success": True,
                "file": str(file_path),
                "backup": str(backup),
                "time": datetime.now().isoformat()
            }

            self.history.append(
                report
            )

            return report

        except Exception as e:

            shutil.copy2(
                backup,
                file_path
            )

            return {
                "success": False,
                "error": str(e),
                "rollback": True
            }

    def history(self):

        return self.history
