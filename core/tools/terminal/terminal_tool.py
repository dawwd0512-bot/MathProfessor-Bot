from datetime import datetime
import subprocess

from core.tools.registry import register


@register
class TerminalTool:

    name = "terminal"

    ALLOWED_COMMANDS = {
        "pwd",
        "ls",
        "git",
        "python",
        "python3",
        "pip",
        "pip3",
    }

    def execute(self, command):

        if not command:
            return {
                "success": False,
                "error": "Empty command"
            }

        command = command.strip()

        executable = command.split()[0]

        if executable not in self.ALLOWED_COMMANDS:
            return {
                "success": False,
                "tool": self.name,
                "error": f"Command '{executable}' not allowed"
            }

        try:

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            return {
                "success": result.returncode == 0,
                "tool": self.name,
                "command": command,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
                "time": datetime.now().isoformat()
            }

        except Exception as e:

            return {
                "success": False,
                "tool": self.name,
                "error": str(e)
            }
