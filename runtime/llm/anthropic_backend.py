"""Anthropic Messages API backend."""
import json
import os
from typing import Optional

from .base import LLMBackend, ChatResponse, ToolCall, ToolDefinition

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class AnthropicBackend(LLMBackend):
    def __init__(self, model: str = "", api_key: str = "", base_url: str = "",
                 max_tokens: int = 4096, temperature: float = 0.0):
        super().__init__(model, api_key, base_url, max_tokens, temperature)
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

        client_kwargs = {"api_key": self.api_key} if self.api_key else {}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = anthropic.AsyncAnthropic(**client_kwargs)

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
    ) -> ChatResponse:
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": self._convert_messages(messages),
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [t.to_anthropic() for t in tools]

        response = await self.client.messages.create(**kwargs)
        return self._parse_response(response)

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert unified message format to Anthropic format."""
        converted = []
        for msg in messages:
            role = msg["role"]
            if role == "tool":
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": str(msg["content"]),
                    }],
                })
            elif role == "assistant" and msg.get("tool_calls"):
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc["arguments"],
                    })
                converted.append({"role": "assistant", "content": content})
            else:
                converted.append({"role": role, "content": msg.get("content", "")})
        return converted

    def _parse_response(self, response) -> ChatResponse:
        content_text = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else json.loads(block.input),
                ))

        return ChatResponse(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason="tool_use" if response.stop_reason == "tool_use" else "end_turn",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw={"id": response.id, "model": response.model},
        )

    async def close(self):
        await self.client.close()
