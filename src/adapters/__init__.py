from .base import GenerationResult, LLMAdapter
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter
from .gemini_adapter import GeminiAdapter
from .nvidia_nim_adapter import NvidiaNimAdapter

_REGISTRY = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "gemini": GeminiAdapter,
    "nvidia_nim": NvidiaNimAdapter,
}


def build_adapter(provider: str, model: str) -> LLMAdapter:
    try:
        adapter_cls = _REGISTRY[provider]
    except KeyError:
        raise ValueError(f"Unknown provider '{provider}'. Available: {list(_REGISTRY)}")
    return adapter_cls(model=model)


__all__ = [
    "LLMAdapter",
    "GenerationResult",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "GeminiAdapter",
    "NvidiaNimAdapter",
    "build_adapter",
]
