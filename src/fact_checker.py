import json
import re

from .adapters import build_adapter
from .models import ClaimFlag, Statement


class FactCheckerAgent:
    """Neutral 5th role (adversarial mode only). Doesn't argue a side — flags
    unsupported claims made by debaters each round. Runs on a cheaper/faster
    model by default since the task (flag claims) is simpler than open debate."""

    def __init__(self, agent_id: str = "fact_checker", provider: str = "anthropic", model: str = "claude-haiku-4-5"):
        self.agent_id = agent_id
        self._adapter = build_adapter(provider, model)
        self.call_count = 0

    def check_round(self, topic: str, round_statements: list[Statement]) -> list[ClaimFlag]:
        if not round_statements:
            return []
        formatted = "\n\n".join(f"{s.agent_id}: {s.content}" for s in round_statements)
        system = (
            "You are a neutral fact-checker in a debate. You do not argue a side. "
            "Your only job is to flag claims stated as fact but not backed by evidence "
            "or reasoning within the statement itself."
        )
        user = (
            f"Debate topic: {topic}\n\n"
            f"Statements made this round:\n{formatted}\n\n"
            "List any unsupported factual claims. Respond with ONLY valid JSON:\n"
            '{"flags": [{"agent_id": "<id>", "claim": "<quoted or paraphrased claim>", '
            '"reason": "<why it is unsupported>"}, ...]}\n'
            "If there are no unsupported claims, respond with {\"flags\": []}."
        )
        self.call_count += 1
        raw = self._adapter.generate(system, user, temperature=0.0)
        parsed = self._parse_json(raw)
        round_num = round_statements[0].round
        return [
            ClaimFlag(agent_id=f["agent_id"], round=round_num, claim=f["claim"], reason=f["reason"])
            for f in parsed.get("flags", [])
        ]

    @staticmethod
    def _parse_json(raw: str) -> dict:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
