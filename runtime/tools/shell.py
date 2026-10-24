"""Shell tool — execute bash commands."""
import asyncio
import os
from .registry import Tool


class ShellTool(Tool):
    name = "shell"
    description = "Execute a bash command and return its output. Use for running CLI tools, scripts, and system commands."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 120)",
                "default": 120,
            },
        },
        "required": ["command"],
    }

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    async def execute(self, args: dict) -> str:
        command = args.get("command", "")
        timeout = args.get("timeout", 120)

        if not command.strip():
            return '{"error": "Empty command"}'

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            output = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")

            result = output
            if err:
                result += f"\nSTDERR:\n{err}"
            if proc.returncode != 0:
                result += f"\n[exit code: {proc.returncode}]"

            return result or "(no output)"

        except asyncio.TimeoutError:
            proc.kill()
            return f'{{"error": "Command timed out after {timeout}s"}}'
        except Exception as e:
            return f'{{"error": "{str(e)}"}}'
