"""Audit logger middleware — logs all tool calls for forensics."""
import json
import logging
import os
import time
from .base import Middleware

logger = logging.getLogger("sharingan.audit")


class AuditLoggerMiddleware(Middleware):
    def __init__(self, log_dir: str = ""):
        self.log_dir = log_dir or os.environ.get("SHARINGAN_LOG_DIR", "/tmp/sharingan_audit")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "tool_calls.jsonl")

    async def post_tool(self, agent_name: str, tool_name: str, args: dict, result: str):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent": agent_name,
            "tool": tool_name,
            "args_keys": list(args.keys()),
            "result_length": len(result) if result else 0,
        }

        # Log extra detail for security-relevant tools
        if tool_name in ("http_request", "nuclei", "ffuf", "katana"):
            entry["target"] = args.get("url", args.get("target", ""))
        elif tool_name == "shell":
            entry["command_prefix"] = args.get("command", "")[:100]
        elif tool_name == "write_file":
            entry["path"] = args.get("path", "")

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Audit log write failed: {e}")
