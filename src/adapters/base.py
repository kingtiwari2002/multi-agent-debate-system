from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float


class LLMAdapter(ABC):
    """Provider-agnostic interface every model backend must implement."""

    @abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.7) -> GenerationResult:
        """Send a single system+user prompt. Returns the model's text response plus
        real (not estimated) token usage and wall-clock latency for that one call,
        as reported by the provider's own API response — used for cost/latency
        tracking, not just the generated text."""
        raise NotImplementedError
