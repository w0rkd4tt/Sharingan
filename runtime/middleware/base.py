"""Middleware base class — intercepts tool calls before/after execution."""
from abc import ABC


class Middleware(ABC):
    async def pre_tool(self, agent_name: str, tool_name: str, args: dict) -> dict:
        """Called before tool execution. Return {"blocked": True, "reason": "..."} to block,
        or {"modified_args": {...}} to rewrite args, or {} to pass through."""
        return {}

    async def post_tool(self, agent_name: str, tool_name: str, args: dict, result: str):
        """Called after tool execution. For logging, auditing, etc."""
        pass
