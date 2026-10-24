"""Scope guard middleware — blocks out-of-scope requests."""
import json
import os
import re
from .base import Middleware

LOCAL_RE = re.compile(
    r"(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[?::1\]?"
    r"|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)",
    re.I,
)
URL_RE = re.compile(r'https?://([^/\s:]+)', re.I)


class ScopeGuardMiddleware(Middleware):
    def __init__(self, scope_file: str = ""):
        self.scope = None
        if scope_file and os.path.exists(scope_file):
            with open(scope_file) as f:
                self.scope = json.load(f)

    def _is_in_scope(self, host: str) -> bool:
        if not self.scope:
            return True
        host = host.lower()

        out_scope = self.scope.get("out_of_scope", [])
        for p in out_scope:
            p = (p.get("asset", p) if isinstance(p, dict) else p).lower().strip()
            if p and (host == p or host.endswith("." + p)):
                return False

        in_scope = self.scope.get("in_scope", self.scope.get("domains", []))
        for p in in_scope:
            p = (p.get("asset", p) if isinstance(p, dict) else p).lower().strip()
            if p.startswith("*."):
                if host.endswith(p[1:]) or host == p[2:]:
                    return True
            elif host == p or host.endswith("." + p):
                return True

        return len(in_scope) == 0

    async def pre_tool(self, agent_name: str, tool_name: str, args: dict) -> dict:
        if not self.scope:
            return {}

        text_to_check = ""
        if tool_name == "shell":
            text_to_check = args.get("command", "")
        elif tool_name == "http_request":
            text_to_check = args.get("url", "")
        elif tool_name in ("nuclei", "ffuf", "katana"):
            text_to_check = args.get("target", args.get("url", ""))
        else:
            return {}

        hosts = URL_RE.findall(text_to_check)
        blocked = []
        for host in hosts:
            if not LOCAL_RE.search(host) and not self._is_in_scope(host):
                blocked.append(host)

        if blocked:
            return {
                "blocked": True,
                "reason": f"SCOPE GUARD: out-of-scope host(s): {', '.join(blocked)}",
            }
        return {}
