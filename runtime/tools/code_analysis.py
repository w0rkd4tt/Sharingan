"""Code analysis tools — semgrep wrapper."""
import asyncio
import json
from .registry import Tool


class SemgrepTool(Tool):
    name = "semgrep"
    description = "Run semgrep static analysis on source code."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Path to scan"},
            "rules": {"type": "string", "description": "Semgrep rule config (e.g. 'p/security-audit')", "default": "p/security-audit"},
            "lang": {"type": "string", "description": "Language filter", "default": ""},
        },
        "required": ["target"],
    }

    async def execute(self, args: dict) -> str:
        target = args["target"]
        rules = args.get("rules", "p/security-audit")
        lang = args.get("lang", "")

        cmd = f"semgrep --json --config '{rules}'"
        if lang:
            cmd += f" --lang {lang}"
        cmd += f" '{target}' 2>/dev/null"

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)

        result = stdout.decode("utf-8", errors="replace")
        try:
            data = json.loads(result)
            findings = data.get("results", [])
            if not findings:
                return "(no findings)"

            lines = []
            for f in findings[:50]:
                sev = f.get("extra", {}).get("severity", "?")
                msg = f.get("extra", {}).get("message", "")
                path = f.get("path", "")
                line = f.get("start", {}).get("line", 0)
                rule = f.get("check_id", "")
                lines.append(f"[{sev}] {path}:{line} — {rule}: {msg[:120]}")
            return "\n".join(lines)
        except json.JSONDecodeError:
            return result or "(no output)"
