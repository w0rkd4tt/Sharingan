from .base import LLMBackend, ChatResponse, ToolCall, ToolDefinition
from .anthropic_backend import AnthropicBackend
from .openai_backend import OpenAIBackend
from .ollama_backend import OllamaBackend

def create_backend(provider: str, **kwargs) -> LLMBackend:
    """Factory to create LLM backend by provider name."""
    providers = {
        "anthropic": AnthropicBackend,
        "openai": OpenAIBackend,
        "ollama": OllamaBackend,
    }
    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(providers.keys())}")
    return providers[provider](**kwargs)
