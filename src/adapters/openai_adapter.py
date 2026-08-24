import os

from openai import OpenAI

from .base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content
