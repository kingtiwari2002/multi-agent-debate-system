import difflib
import math
import os


class RepetitionDetector:
    """Flags an agent as repeating itself when its current statement is too
    similar to its own immediately-preceding statement. Uses OpenAI embeddings
    for cosine similarity when OPENAI_API_KEY is available, falling back to a
    plain text similarity ratio otherwise (keeps Phase 2 usable with a single
    provider configured)."""

    def __init__(self, threshold: float = 0.92):
        self.threshold = threshold
        self._embedding_client = None
        if os.environ.get("OPENAI_API_KEY"):
            from openai import OpenAI

            self._embedding_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def is_repeating(self, previous: str, current: str) -> tuple[bool, float]:
        score = self._similarity(previous, current)
        return score >= self.threshold, score

    def _similarity(self, a: str, b: str) -> float:
        if self._embedding_client is not None:
            try:
                return self._cosine_similarity_via_embeddings(a, b)
            except Exception:
                pass
        return difflib.SequenceMatcher(None, a, b).ratio()

    def _cosine_similarity_via_embeddings(self, a: str, b: str) -> float:
        response = self._embedding_client.embeddings.create(model="text-embedding-3-small", input=[a, b])
        vec_a, vec_b = response.data[0].embedding, response.data[1].embedding
        dot = sum(x * y for x, y in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(x * x for x in vec_a))
        norm_b = math.sqrt(sum(y * y for y in vec_b))
        return dot / (norm_a * norm_b)
