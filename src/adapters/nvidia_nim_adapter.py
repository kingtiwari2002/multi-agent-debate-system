import os
import time

from openai import OpenAI

from .base import GenerationResult, LLMAdapter


class NvidiaNimAdapter(LLMAdapter):
    """NVIDIA NIM-hosted models, reached through NVIDIA's OpenAI-compatible
    endpoint (https://integrate.api.nvidia.com/v1) — same request/response
    shape as OpenAIAdapter, different base URL and key."""

    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self, model: str = "nvidia/llama-3.1-nemotron-super-49b-v1"):
        self.model = model
        self._client = OpenAI(api_key=os.environ["NVIDIA_API_KEY"], base_url=self.BASE_URL)

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
