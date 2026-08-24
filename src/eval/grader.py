from ..adapters import build_adapter


class AnswerGrader:
    """LLM-graded correctness check — robust to phrasing differences that a
    plain substring match on the known correct answer would miss."""

    def __init__(self, provider: str = "anthropic", model: str = "claude-haiku-4-5"):
        self._adapter = build_adapter(provider, model)

    def is_correct(self, question: str, correct_answer: str, candidate_text: str) -> bool:
        if not candidate_text.strip():
            return False
        system = "You are a strict grader. Respond with only YES or NO."
        user = (
            f"Question: {question}\n"
            f"Known correct answer: {correct_answer}\n"
            f"Candidate response: {candidate_text}\n\n"
            "Does the candidate response arrive at the correct answer, even if phrased "
            "differently or embedded in a longer explanation? Answer YES or NO only."
        )
        raw = self._adapter.generate(system, user, temperature=0.0)
        return raw.strip().upper().startswith("Y")
