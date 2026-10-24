"""UA injector middleware — ensures browser User-Agent on HTTP tools."""
import json
import os
import re
from .base import Middleware


class UAInjectorMiddleware(Middleware):
    def __init__(self):
        self.ua = self._load_ua()

    def _load_ua(self) -> str:
        ua_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "user-agents.json"
        )
        try:
            with open(ua_path) as f:
                data = json.load(f)
            profile = data.get("default_profile", "chrome")
            return data["profiles"][profile]
        except Exception:
            return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36")

    async def pre_tool(self, agent_name: str, tool_name: str, args: dict) -> dict:
        if tool_name == "http_request":
            headers = args.get("headers", {})
            if "User-Agent" not in headers and "user-agent" not in headers:
                headers["User-Agent"] = self.ua
                return {"modified_args": {**args, "headers": headers}}

        elif tool_name == "shell":
            cmd = args.get("command", "")
            curl_cmds = ("curl", "wget", "httpx")
            if any(cmd.strip().startswith(c) for c in curl_cmds):
                if "-H" not in cmd or "User-Agent" not in cmd:
                    if cmd.strip().startswith("curl"):
                        modified = cmd.rstrip() + f" -H 'User-Agent: {self.ua}'"
                        return {"modified_args": {**args, "command": modified}}

        return {}
