"""Ollama / local model backend. Also supports vLLM, llama.cpp OpenAI-compat servers."""
import json
import os
from typing import Optional

from .base import LLMBackend, ChatResponse, ToolCall, ToolDefinition

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class OllamaBackend(LLMBackend):
    """Ollama native API + OpenAI-compatible fallback for vLLM/llama.cpp."""

    def __init__(self, model: str = "", api_key: str = "", base_url: str = "",
                 max_tokens: int = 4096, temperature: float = 0.0,
                 mode: str = "ollama"):
        super().__init__(model, api_key, base_url, max_tokens, temperature)
        if not HAS_HTTPX:
            raise ImportError("httpx package not installed. Run: pip install httpx")

        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1")
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.mode = mode  # "ollama" native or "openai_compat" for vLLM/llama.cpp
        self.client = httpx.AsyncClient(timeout=300.0)

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
    ) -> ChatResponse:
        if self.mode == "openai_compat":
            return await self._chat_openai_compat(messages, tools, system)
        return await self._chat_ollama_native(messages, tools, system)

    async def _chat_ollama_native(
        self, messages, tools, system
    ) -> ChatResponse:
        ollama_messages = []
        if system:
            ollama_messages.append({"role": "system", "content": system})

        for msg in messages:
            if msg["role"] == "tool":
                ollama_messages.append({
                    "role": "tool",
                    "content": str(msg["content"]),
                })
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                ollama_messages.append({
                    "role": "assistant",
                    "content": msg.get("content", ""),
                    "tool_calls": [{
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    } for tc in msg["tool_calls"]],
                })
            else:
                ollama_messages.append({
                    "role": msg["role"],
                    "content": msg.get("content", ""),
                })

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if tools:
            payload["tools"] = [{
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            } for t in tools]

        resp = await self.client.post(
            f"{self.base_url}/api/chat", json=payload
        )
        resp.raise_for_status()
        data = resp.json()

        msg_data = data.get("message", {})
        tool_calls = []
        for tc in msg_data.get("tool_calls", []):
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append(ToolCall(
                id=f"call_{hash(func.get('name', '')) % 10**8:08d}",
                name=func.get("name", ""),
                arguments=args,
            ))

        return ChatResponse(
            content=msg_data.get("content", ""),
            tool_calls=tool_calls,
            stop_reason="tool_use" if tool_calls else "end_turn",
            usage={
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
            },
            raw=data,
        )

    async def _chat_openai_compat(
        self, messages, tools, system
    ) -> ChatResponse:
        """OpenAI-compatible endpoint (vLLM, llama.cpp, LM Studio, etc.)."""
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})

        for msg in messages:
            if msg["role"] == "tool":
                oai_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.get("tool_call_id", ""),
                    "content": str(msg["content"]),
                })
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                oai_msg = {"role": "assistant", "content": msg.get("content") or None}
                oai_msg["tool_calls"] = [{
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"]),
                    },
                } for tc in msg["tool_calls"]]
                oai_messages.append(oai_msg)
            else:
                oai_messages.append({
                    "role": msg["role"],
                    "content": msg.get("content", ""),
                })

        payload = {
            "model": self.model,
            "messages": oai_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = [t.to_openai() for t in tools]

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload, headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        msg_data = choice["message"]

        tool_calls = []
        for tc in msg_data.get("tool_calls") or []:
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                arguments=args,
            ))

        usage = data.get("usage", {})
        return ChatResponse(
            content=msg_data.get("content") or "",
            tool_calls=tool_calls,
            stop_reason="tool_use" if tool_calls else "end_turn",
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
            raw=data,
        )

    async def close(self):
        await self.client.aclose()
