"""OpenAI Chat Completions API backend (also compatible with Azure, Together, etc.)."""
import json
import os
from typing import Optional

from .base import LLMBackend, ChatResponse, ToolCall, ToolDefinition

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class OpenAIBackend(LLMBackend):
    def __init__(self, model: str = "", api_key: str = "", base_url: str = "",
                 max_tokens: int = 4096, temperature: float = 0.0):
        super().__init__(model, api_key, base_url, max_tokens, temperature)
        if not HAS_OPENAI:
            raise ImportError("openai package not installed. Run: pip install openai")

        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

        client_kwargs = {}
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        if base_url:
            client_kwargs["base_url"] = base_url
        elif os.environ.get("OPENAI_BASE_URL"):
            client_kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]

        self.client = openai.AsyncOpenAI(**client_kwargs)

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
    ) -> ChatResponse:
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(self._convert_messages(messages))

        kwargs = {
            "model": self.model,
            "messages": oai_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            kwargs["tools"] = [t.to_openai() for t in tools]

        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        converted = []
        for msg in messages:
            role = msg["role"]
            if role == "tool":
                converted.append({
                    "role": "tool",
                    "tool_call_id": msg["tool_call_id"],
                    "content": str(msg["content"]),
                })
            elif role == "assistant" and msg.get("tool_calls"):
                oai_msg = {"role": "assistant", "content": msg.get("content") or None}
                oai_msg["tool_calls"] = [{
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"]),
                    },
                } for tc in msg["tool_calls"]]
                converted.append(oai_msg)
            else:
                converted.append({"role": role, "content": msg.get("content", "")})
        return converted

    def _parse_response(self, response) -> ChatResponse:
        choice = response.choices[0]
        msg = choice.message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                ))

        return ChatResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            stop_reason="tool_use" if choice.finish_reason == "tool_calls" else "end_turn",
            usage={
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            },
            raw={"id": response.id, "model": response.model},
        )

    async def close(self):
        await self.client.close()
