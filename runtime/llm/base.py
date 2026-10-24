"""Abstract LLM backend — the contract all providers implement."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolDefinition:
    """A tool the LLM can call."""
    name: str
    description: str
    parameters: dict  # JSON Schema for the tool's parameters

    def to_anthropic(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict


@dataclass
class ChatResponse:
    """Unified response from any LLM backend."""
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"  # end_turn | tool_use | max_tokens | error
    usage: dict = field(default_factory=dict)  # {input_tokens, output_tokens}
    raw: Optional[dict] = None  # provider-specific raw response

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMBackend(ABC):
    """Abstract LLM backend. All providers implement this."""

    def __init__(self, model: str = "", api_key: str = "", base_url: str = "",
                 max_tokens: int = 4096, temperature: float = 0.0):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
    ) -> ChatResponse:
        """Send messages and get a response, possibly with tool calls.

        messages: list of {"role": "user"|"assistant"|"tool", "content": str, ...}
        tools: available tools the LLM can call
        system: system prompt (separate from messages for providers that support it)
        """

    @abstractmethod
    async def close(self):
        """Cleanup resources."""

    def count_message_tokens(self, messages: list[dict]) -> int:
        """Rough token estimate. Override for accurate counting."""
        text = "".join(str(m.get("content", "")) for m in messages)
        return len(text) // 4  # rough estimate
