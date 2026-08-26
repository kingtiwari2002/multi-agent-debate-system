import json
import re

from .adapters import build_adapter
from .models import AgentConfig, JudgeVerdict, Statement
from .pricing import estimate_cost_usd


def _parse_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _format_transcript(transcript: list[Statement]) -> str:
    return "\n\n".join(f"[Round {s.round} / {s.phase}] {s.agent_id}: {s.content}" for s in transcript)


class RubricJudge:
    """Judge A. Scores each agent against a fixed rubric: factual accuracy,
    logical validity, responsiveness to the opponent's strongest point, and
    clarity. Outputs numeric scores, not just a winner."""

    JUDGE_ID = "judge_a_rubric"

    def __init__(self, provider: str = "anthropic", model: str = "claude-sonnet-5"):
        self.provider = provider
        self.model = model
        self._adapter = build_adapter(provider, model)
        self.call_count = 0

    def judge(self, topic: str, agents: list[AgentConfig], transcript: list[Statement]) -> JudgeVerdict:
        agent_ids = [a.agent_id for a in agents if a.role == "debater"]
        system = (
            "You are an impartial debate judge. Score strictly against the rubric. "
            "Do not favor an agent for rhetorical style alone."
        )
        user = (
            f"Debate topic: {topic}\n"
            f"Participants: {', '.join(agent_ids)}\n\n"
            f"Full transcript:\n{_format_transcript(transcript)}\n\n"
            "For EACH participant, score 1-10 on: factual_accuracy, logical_validity, "
            "responsiveness, clarity. Then declare an overall winner.\n\n"
            "Respond with ONLY valid JSON in this exact shape:\n"
            "{\n"
            '  "scores": {"<agent_id>": {"factual_accuracy": n, "logical_validity": n, '
            '"responsiveness": n, "clarity": n}, ...},\n'
            '  "winner": "<agent_id>",\n'
            '  "reasoning": "<2-3 sentence justification>"\n'
            "}"
        )
        self.call_count += 1
        result = self._adapter.generate(system, user, temperature=0.0)
        parsed = _parse_json(result.text)
        return JudgeVerdict(
            judge_id=self.JUDGE_ID,
            scores=parsed.get("scores", {}),
            winner=parsed.get("winner", ""),
            reasoning=parsed.get("reasoning", result.text),
            latency_seconds=result.latency_seconds,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=estimate_cost_usd(self.provider, self.model, result.input_tokens, result.output_tokens),
        )


class AdversarialAuditorJudge:
    """Judge B. Doesn't score rounds — hunts for the single weakest unrefuted
    point and the single strongest unrefuted point across the whole debate,
    then verdicts based on which side has more unresolved weaknesses. A
    different lens than Judge A, catching different failure modes."""

    JUDGE_ID = "judge_b_auditor"

    def __init__(self, provider: str = "openai", model: str = "gpt-4o"):
        self.provider = provider
        self.model = model
        self._adapter = build_adapter(provider, model)
        self.call_count = 0

    def judge(self, topic: str, agents: list[AgentConfig], transcript: list[Statement]) -> JudgeVerdict:
        agent_ids = [a.agent_id for a in agents if a.role == "debater"]
        system = (
            "You are an adversarial debate auditor. You do not score rounds. Your job is to "
            "find the single strongest point that was never refuted, and the single weakest "
            "point that was never refuted, across the entire debate. Verdict goes to whichever "
            "side carries fewer unresolved weaknesses."
        )
        user = (
            f"Debate topic: {topic}\n"
            f"Participants: {', '.join(agent_ids)}\n\n"
            f"Full transcript:\n{_format_transcript(transcript)}\n\n"
            "Respond with ONLY valid JSON in this exact shape:\n"
            "{\n"
            '  "strongest_unrefuted_point": {"agent_id": "<id>", "point": "<summary>"},\n'
            '  "weakest_unrefuted_point": {"agent_id": "<id>", "point": "<summary>"},\n'
            '  "winner": "<agent_id>",\n'
            '  "reasoning": "<2-3 sentence justification tied to unresolved weaknesses>"\n'
            "}"
        )
        self.call_count += 1
        result = self._adapter.generate(system, user, temperature=0.0)
        parsed = _parse_json(result.text)
        return JudgeVerdict(
            judge_id=self.JUDGE_ID,
            scores={
                "strongest_unrefuted_point": parsed.get("strongest_unrefuted_point", {}),
                "weakest_unrefuted_point": parsed.get("weakest_unrefuted_point", {}),
            },
            winner=parsed.get("winner", ""),
            reasoning=parsed.get("reasoning", result.text),
            latency_seconds=result.latency_seconds,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=estimate_cost_usd(self.provider, self.model, result.input_tokens, result.output_tokens),
        )
