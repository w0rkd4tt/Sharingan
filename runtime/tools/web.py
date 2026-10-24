"""HTTP request tool — makes web requests with UA enforcement."""
import asyncio
import json
import os
from .registry import Tool


class HttpRequestTool(Tool):
    name = "http_request"
    description = "Make an HTTP request (GET, POST, etc.) and return the response."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Target URL"},
            "method": {"type": "string", "description": "HTTP method", "default": "GET",
                      "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]},
            "headers": {"type": "object", "description": "Request headers", "default": {}},
            "body": {"type": "string", "description": "Request body for POST/PUT", "default": ""},
            "follow_redirects": {"type": "boolean", "default": True},
            "timeout": {"type": "integer", "default": 30},
        },
        "required": ["url"],
    }

    def _get_ua(self) -> str:
        ua_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "user-agents.json")
        try:
            with open(ua_path) as f:
                data = json.load(f)
            profile = data.get("default_profile", "chrome")
            return data.get("profiles", {}).get(profile, "")
        except Exception:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    async def execute(self, args: dict) -> str:
        url = args["url"]
        method = args.get("method", "GET")
        headers = args.get("headers", {})
        body = args.get("body", "")
        timeout = args.get("timeout", 30)
        follow = args.get("follow_redirects", True)

        if "User-Agent" not in headers and "user-agent" not in headers:
            headers["User-Agent"] = self._get_ua()

        cmd_parts = ["curl", "-s", "-w", r"\n---HTTP_CODE:%{http_code}---"]
        cmd_parts.extend(["-X", method])

        if not follow:
            cmd_parts.append("--max-redirs 0")

        cmd_parts.extend(["-m", str(timeout)])
        cmd_parts.append("-i")  # include headers

        for k, v in headers.items():
            cmd_parts.extend(["-H", f"{k}: {v}"])

        if body and method in ("POST", "PUT", "PATCH"):
            cmd_parts.extend(["-d", body])

        cmd_parts.append(url)

        cmd = " ".join(f"'{p}'" if " " in p or ":" in p else p for p in cmd_parts)

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 5)

        result = stdout.decode("utf-8", errors="replace")
        if stderr:
            err = stderr.decode("utf-8", errors="replace")
            if err.strip():
                result += f"\n\nCURL ERROR: {err}"

        return result
