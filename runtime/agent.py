"""Agent — autonomous tool-using agent with middleware enforcement."""
import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from .llm.base import LLMBackend, ChatResponse, ToolCall, ToolDefinition

logger = logging.getLogger("sharingan.agent")


@dataclass
class AgentResult:
    """Result from an agent run."""
    content: str = ""
    tool_calls_made: int = 0
    tokens_used: dict = field(default_factory=dict)
    duration_seconds: float = 0
    error: Optional[str] = None


class Agent:
    """An autonomous agent: system prompt + tools + LLM + middleware → action loop."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: LLMBackend,
        tools: Optional[list] = None,
        middleware: Optional[list] = None,
        max_turns: int = 50,
        max_tokens_total: int = 200_000,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm
        self.tools = tools or []
        self.middleware = middleware or []
        self.max_turns = max_turns
        self.max_tokens_total = max_tokens_total
        self._tool_defs = [t.definition for t in self.tools]

    async def run(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Run the agent loop until completion or budget exhaustion."""
        start = time.time()
        tokens_total = {"input": 0, "output": 0}
        tool_calls_count = 0

        user_content = task
        if context:
            user_content += f"\n\n<context>\n{json.dumps(context, indent=2, ensure_ascii=False)}\n</context>"

        messages = [{"role": "user", "content": user_content}]

        for turn in range(self.max_turns):
            if tokens_total["input"] + tokens_total["output"] > self.max_tokens_total:
                logger.warning(f"[{self.name}] Token budget exhausted at turn {turn}")
                break

            try:
                response = await self.llm.chat(
                    messages=messages,
                    tools=self._tool_defs if self._tool_defs else None,
                    system=self.system_prompt,
                )
            except Exception as e:
                logger.error(f"[{self.name}] LLM error: {e}")
                return AgentResult(
                    error=str(e),
                    tool_calls_made=tool_calls_count,
                    tokens_used=tokens_total,
                    duration_seconds=time.time() - start,
                )

            tokens_total["input"] += response.usage.get("input_tokens", 0)
            tokens_total["output"] += response.usage.get("output_tokens", 0)

            if not response.has_tool_calls:
                return AgentResult(
                    content=response.content,
                    tool_calls_made=tool_calls_count,
                    tokens_used=tokens_total,
                    duration_seconds=time.time() - start,
                )

            assistant_msg = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in response.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for tc in response.tool_calls:
                tool_calls_count += 1
                result = await self._execute_tool(tc)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        return AgentResult(
            content="Agent reached max turns without completing.",
            tool_calls_made=tool_calls_count,
            tokens_used=tokens_total,
            duration_seconds=time.time() - start,
        )

    async def _execute_tool(self, tool_call: ToolCall) -> str:
        """Execute a tool call, passing through middleware chain."""
        for mw in self.middleware:
            decision = await mw.pre_tool(self.name, tool_call.name, tool_call.arguments)
            if decision.get("blocked"):
                reason = decision.get("reason", "Blocked by middleware")
                logger.warning(f"[{self.name}] Tool {tool_call.name} blocked: {reason}")
                return json.dumps({"error": reason, "blocked": True})

            if decision.get("modified_args"):
                tool_call.arguments = decision["modified_args"]

        tool = self._find_tool(tool_call.name)
        if not tool:
            return json.dumps({"error": f"Unknown tool: {tool_call.name}"})

        try:
            result = await tool.execute(tool_call.arguments)
        except Exception as e:
            logger.error(f"[{self.name}] Tool {tool_call.name} error: {e}")
            result = json.dumps({"error": str(e)})

        for mw in self.middleware:
            await mw.post_tool(self.name, tool_call.name, tool_call.arguments, result)

        if isinstance(result, str) and len(result) > 50_000:
            result = result[:50_000] + "\n\n[TRUNCATED — output exceeded 50KB]"

        return result

    def _find_tool(self, name: str):
        for t in self.tools:
            if t.name == name:
                return t
        return None


def load_prompt(prompt_path: str) -> str:
    """Load an agent prompt from a .md file."""
    with open(prompt_path, "r") as f:
        return f.read()
