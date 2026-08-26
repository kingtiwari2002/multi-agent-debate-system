import os

from google import genai
from google.genai import types

from .base import LLMAdapter


class GeminiAdapter(LLMAdapter):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        response = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system, temperature=temperature),
        )
        return response.text
