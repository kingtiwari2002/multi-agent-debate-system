from .base import LLMAdapter
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter

_REGISTRY = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
}


def build_adapter(provider: str, model: str) -> LLMAdapter:
    try:
        adapter_cls = _REGISTRY[provider]
    except KeyError:
        raise ValueError(f"Unknown provider '{provider}'. Available: {list(_REGISTRY)}")
    return adapter_cls(model=model)


__all__ = ["LLMAdapter", "AnthropicAdapter", "OpenAIAdapter", "build_adapter"]
