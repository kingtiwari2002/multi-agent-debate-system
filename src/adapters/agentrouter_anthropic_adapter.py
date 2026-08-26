import os
import time

from anthropic import Anthropic

from .base import GenerationResult, LLMAdapter


class AgentRouterAnthropicAdapter(LLMAdapter):
    """AgentRouter (https://agentrouter.org), reached through its
    Anthropic-SDK-compatible endpoint instead of the OpenAI-compatible one —
    same request/response shape as AnthropicAdapter, pointed at AgentRouter's
    base URL with AGENTROUTER_API_KEY instead of ANTHROPIC_API_KEY. The
    Anthropic SDK sends `api_key` as the `x-api-key` header by default, which
    is exactly what AgentRouter's Anthropic-compatible endpoint expects — no
    custom header wiring needed beyond base_url + api_key.

    Only used when an agent/judge/fact-checker config explicitly selects
    provider="agentrouter_anthropic" — direct ANTHROPIC_API_KEY/OPENAI_API_KEY
    usage elsewhere in the project is untouched either way."""

    BASE_URL = "https://agentrouter.org/"

    def __init__(self, model: str = "claude-sonnet-5"):
        self.model = model
        self._client = Anthropic(api_key=os.environ["AGENTROUTER_API_KEY"], base_url=self.BASE_URL)

    def generate(self, system: str, user: str, temperature: float = 0.7) -> GenerationResult:
        start = time.perf_counter()
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency = time.perf_counter() - start
        return GenerationResult(
            text=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_seconds=latency,
        )
