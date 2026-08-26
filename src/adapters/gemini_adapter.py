import os
import time

from google import genai
from google.genai import types

from .base import GenerationResult, LLMAdapter


class GeminiAdapter(LLMAdapter):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def generate(self, system: str, user: str, temperature: float = 0.7) -> GenerationResult:
        start = time.perf_counter()
        response = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system, temperature=temperature),
        )
        latency = time.perf_counter() - start
        usage = response.usage_metadata
        return GenerationResult(
            text=response.text,
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=usage.candidates_token_count or 0,
            latency_seconds=latency,
        )
