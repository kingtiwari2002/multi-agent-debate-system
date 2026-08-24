from ..adapters import build_adapter


class SingleAgentBaseline:
    """The thing the 5-agent + 2-judge system has to beat: one model, one call."""

    def __init__(self, provider: str = "anthropic", model: str = "claude-sonnet-5"):
        self._adapter = build_adapter(provider, model)

    def answer(self, question: str) -> str:
        system = "Answer the question directly and concisely. Give your final answer clearly."
        return self._adapter.generate(system, question, temperature=0.0)
