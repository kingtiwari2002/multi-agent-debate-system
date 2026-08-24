import os

from anthropic import Anthropic

from .base import LLMAdapter


class AnthropicAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-sonnet-5"):
        self.model = model
        self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text
