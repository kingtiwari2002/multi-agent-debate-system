import os
import time

from openai import OpenAI

from .base import GenerationResult, LLMAdapter


class AgentRouterAdapter(LLMAdapter):
    """AgentRouter (https://agentrouter.org) — optional third-party gateway,
    reached through its OpenAI-compatible endpoint. Same request/response
    shape as OpenAIAdapter, different base URL and key; AgentRouter itself
    routes to the right backend model by the `model` name passed through
    (Claude, GPT, etc. — whatever the caller already configured), so no
    model-name translation happens here.

    Only used when an agent/judge/fact-checker config explicitly selects
    provider="agentrouter" — direct ANTHROPIC_API_KEY/OPENAI_API_KEY usage
    elsewhere in the project is untouched either way."""

    BASE_URL = "https://agentrouter.org/v1"

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self._client = OpenAI(api_key=os.environ["AGENTROUTER_API_KEY"], base_url=self.BASE_URL)

    def generate(self, system: str, user: str, temperature: float = 0.7) -> GenerationResult:
        start = time.perf_counter()
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        latency = time.perf_counter() - start
        return GenerationResult(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            latency_seconds=latency,
        )
