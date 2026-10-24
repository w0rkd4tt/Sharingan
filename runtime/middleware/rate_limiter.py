"""Rate limiter middleware — token bucket algorithm."""
import time
from .base import Middleware

URL_TOOLS = {"http_request", "nuclei", "ffuf", "katana", "waybackurls", "shell"}


class RateLimiterMiddleware(Middleware):
    def __init__(self, rps: int = 10):
        self.rps = rps
        self.tokens = float(rps)
        self.last_time = time.monotonic()

    async def pre_tool(self, agent_name: str, tool_name: str, args: dict) -> dict:
        if tool_name not in URL_TOOLS:
            return {}

        # Skip for non-network shell commands
        if tool_name == "shell":
            cmd = args.get("command", "")
            network_cmds = ("curl", "wget", "httpx", "nuclei", "ffuf", "katana",
                           "sqlmap", "ghauri", "nikto", "whatweb", "subfinder")
            if not any(cmd.strip().startswith(nc) for nc in network_cmds):
                return {}

        now = time.monotonic()
        elapsed = now - self.last_time
        self.tokens = min(self.rps, self.tokens + elapsed * self.rps)
        self.last_time = now

        if self.tokens < 1:
            wait = (1 - self.tokens) / self.rps
            return {
                "blocked": True,
                "reason": f"RATE LIMITER: too many requests. Wait {wait:.1f}s. Rate: {self.rps} RPS.",
            }

        self.tokens -= 1
        return {}
