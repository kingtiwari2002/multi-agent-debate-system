from .adapters import GenerationResult, build_adapter
from .models import AgentConfig, Statement


class DebateAgent:
    """Independent debater. Sees its own past statements + the public transcript
    of other agents' statements only — never another agent's internal reasoning."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._adapter = build_adapter(config.provider, config.model)
        self.call_count = 0

    def _generate(self, system: str, user: str) -> GenerationResult:
        self.call_count += 1
        return self._adapter.generate(system, user, self.config.temperature)

    def _system_prompt(self) -> str:
        return (
            f"You are {self.config.agent_id}, a debate participant.\n"
            f"Your assigned position: {self.config.position}\n"
            f"Persona: {self.config.persona}\n\n"
            "You must not concede or soften your position unless directly refuted "
            "by a specific factual claim from an opponent. Be concise: 3-5 sentences."
        )

    def _format_transcript(self, transcript: list[Statement]) -> str:
        if not transcript:
            return "(no statements yet)"
        return "\n\n".join(
            f"[Round {s.round} / {s.phase}] {s.agent_id}: {s.content}" for s in transcript
        )

    def opening_statement(self, topic: str) -> GenerationResult:
        user = (
            f"Debate topic: {topic}\n\n"
            "Give your opening statement establishing your position. "
            "Do not reference other agents — none have spoken yet."
        )
        return self._generate(self._system_prompt(), user)

    def rebuttal(self, topic: str, round_num: int, public_transcript: list[Statement], fact_flags: str = "") -> GenerationResult:
        flags_note = f"\n\nFact-checker flagged these unsupported claims — substantiate or withdraw them:\n{fact_flags}" if fact_flags else ""
        user = (
            f"Debate topic: {topic}\n\n"
            f"Public transcript so far:\n{self._format_transcript(public_transcript)}"
            f"{flags_note}\n\n"
            f"This is round {round_num}. Respond to the strongest opposing point made so far — "
            "quote or directly reference it — then reinforce or refine your position."
        )
        return self._generate(self._system_prompt(), user)

    def closing_statement(self, topic: str, public_transcript: list[Statement], unresolved_flags: str = "") -> GenerationResult:
        flags_note = f"\n\nUnresolved fact-check flags to address:\n{unresolved_flags}" if unresolved_flags else ""
        user = (
            f"Debate topic: {topic}\n\n"
            f"Public transcript so far:\n{self._format_transcript(public_transcript)}"
            f"{flags_note}\n\n"
            "Give your final closing statement."
        )
        return self._generate(self._system_prompt(), user)

    def tie_break_response(
        self, topic: str, public_transcript: list[Statement], judge_a_reasoning: str, judge_b_reasoning: str
    ) -> GenerationResult:
        user = (
            f"Debate topic: {topic}\n\n"
            f"Public transcript so far:\n{self._format_transcript(public_transcript)}\n\n"
            "The two judges could not agree on a winner. Their reasoning (not their verdicts) "
            f"was:\n\nJudge A: {judge_a_reasoning}\n\nJudge B: {judge_b_reasoning}\n\n"
            "Give one final rebuttal directly addressing the gaps or weaknesses either judge "
            "identified. This is the last round before re-judgment."
        )
        return self._generate(self._system_prompt(), user)
