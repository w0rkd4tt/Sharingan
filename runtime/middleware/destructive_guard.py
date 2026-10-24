"""Destructive guard middleware — blocks dangerous commands."""
import re
from .base import Middleware

DENY_PATTERNS = [
    (r"\brm\s+(-[rR]f|--recursive)\s+/", "recursive delete of root"),
    (r"\bdd\s+if=", "raw disk write"),
    (r"\bmkfs\b", "filesystem format"),
    (r"\bshutdown\b", "system shutdown"),
    (r"\breboot\b", "system reboot"),
    (r"\bsqlmap\b.*--dump-all\b", "sqlmap full dump"),
    (r"\bsqlmap\b.*--os-shell\b", "sqlmap OS shell"),
    (r"\bmsfconsole\b", "metasploit console"),
    (r"\bmsfvenom\b", "metasploit payload gen"),
    (r"\b:()\s*\{\s*:\|:&\s*\}\s*;:", "fork bomb"),
    (r"\b>\s*/dev/sd[a-z]", "raw device write"),
]


class DestructiveGuardMiddleware(Middleware):
    async def pre_tool(self, agent_name: str, tool_name: str, args: dict) -> dict:
        if tool_name != "shell":
            return {}

        cmd = args.get("command", "")
        for pattern, desc in DENY_PATTERNS:
            if re.search(pattern, cmd, re.I):
                return {
                    "blocked": True,
                    "reason": f"DESTRUCTIVE GUARD: blocked '{desc}'",
                }
        return {}
