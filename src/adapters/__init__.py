from .base import GenerationResult, LLMAdapter
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter
from .gemini_adapter import GeminiAdapter
from .nvidia_nim_adapter import NvidiaNimAdapter
from .agentrouter_adapter import AgentRouterAdapter
from .agentrouter_anthropic_adapter import AgentRouterAnthropicAdapter

_REGISTRY = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "gemini": GeminiAdapter,
    "nvidia_nim": NvidiaNimAdapter,
    # Optional third-party gateway (https://agentrouter.org) — only reachable
    # if an agent/judge/fact-checker config explicitly picks one of these two
    # provider strings; see AGENTROUTER_API_KEY in .env.example.
    "agentrouter": AgentRouterAdapter,
    "agentrouter_anthropic": AgentRouterAnthropicAdapter,
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
    "AgentRouterAdapter",
    "AgentRouterAnthropicAdapter",
    "build_adapter",
]
