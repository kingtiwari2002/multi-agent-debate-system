from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Provider-agnostic interface every model backend must implement."""

    @abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a single system+user prompt and return the model's text response."""
        raise NotImplementedError
