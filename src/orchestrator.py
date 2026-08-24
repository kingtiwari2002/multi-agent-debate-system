import json
import random
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional

from .agent import DebateAgent
from .fact_checker import FactCheckerAgent
from .judge import AdversarialAuditorJudge, RubricJudge
from .judge_stats import record_and_get_disagreement_rate
from .models import AgentConfig, ClaimFlag, DebateRun, JudgeVerdict, Statement
from .repetition import RepetitionDetector

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"

EventCallback = Callable[[dict], None]


class DebateOrchestrator:
    """Drives the round structure, owns the public transcript, runs the
    fact-checker and repetition detector, and combines both judges' verdicts.

    Phase 3 scope: two independent judges (Judge A rubric scorer, Judge B
    adversarial auditor), agreement check, and a capped single tie-break round
    when they disagree. Fixed-round termination only — convergence early-stop
    lands later.

    Phase 5 addition: an optional on_event callback fires as the debate
    progresses (statements, claim flags, drops, verdicts) so a caller — e.g.
    the web backend — can stream a live transcript instead of waiting for the
    full run to finish."""

    def __init__(
        self,
        topic: str,
        agent_configs: list[AgentConfig],
        max_rounds: int = 3,
        mode: str = "adversarial",
        repetition_threshold: float = 0.92,
        on_event: Optional[EventCallback] = None,
        run_id: Optional[str] = None,
    ):
        self.topic = topic
        self.mode = mode
        self.max_rounds = max_rounds
        self.agent_configs = agent_configs
        self.run_id = run_id
        self._on_event = on_event

        debater_configs = [c for c in agent_configs if c.role == "debater"]
        fact_checker_configs = [c for c in agent_configs if c.role == "fact_checker"]

        self.debaters = [DebateAgent(cfg) for cfg in debater_configs]
        self.fact_checker = None
        if mode == "adversarial" and fact_checker_configs:
            fc_cfg = fact_checker_configs[0]
            self.fact_checker = FactCheckerAgent(fc_cfg.agent_id, fc_cfg.provider, fc_cfg.model)

        # Judge B defaults to a different model family than Judge A to reduce
        # self-preference bias (Section 4) — both are also model-distinct from
        # the debater roster where the default presets are used.
        self.judge_a = RubricJudge()
        self.judge_b = AdversarialAuditorJudge()
        self.repetition_detector = RepetitionDetector(threshold=repetition_threshold)

        self.transcript: list[Statement] = []
        self.claim_flags: list[ClaimFlag] = []
        self.dropped_agents: set[str] = set()

    def run(self) -> DebateRun:
        run_id = self.run_id or str(uuid.uuid4())[:8]

        # Round 0 — opening statements, no cross-visibility
        for agent in self.debaters:
            content = agent.opening_statement(self.topic)
            self._append_statement(Statement(agent.config.agent_id, round=0, phase="opening", content=content))

        # Rounds 1..max_rounds-1 — rebuttals
        for round_num in range(1, self.max_rounds):
            active_flags_text = self._format_pending_flags()
            order = self._active_debaters()
            random.shuffle(order)

            round_statements: list[Statement] = []
            for agent in order:
                content = agent.rebuttal(self.topic, round_num, list(self.transcript), active_flags_text)
                statement = Statement(agent.config.agent_id, round=round_num, phase="rebuttal", content=content)

                if self._check_and_apply_repetition(agent, statement):
                    continue

                self._append_statement(statement)
                round_statements.append(statement)

            if self.fact_checker and round_statements:
                new_flags = self.fact_checker.check_round(self.topic, round_statements)
                if new_flags:
                    self.claim_flags.extend(new_flags)
                    self._emit("claim_flags", flags=[asdict(f) for f in new_flags])

        # Final round — closing statements
        for agent in self._active_debaters():
            unresolved = self._format_pending_flags()
            content = agent.closing_statement(self.topic, list(self.transcript), unresolved)
            self._append_statement(Statement(agent.config.agent_id, round=self.max_rounds, phase="closing", content=content))

        # Judgment phase — both judges run independently, neither sees the other's verdict.
        verdict_a = self.judge_a.judge(self.topic, self.agent_configs, self.transcript)
        self._emit("judge_verdict", verdict=asdict(verdict_a))
        verdict_b = self.judge_b.judge(self.topic, self.agent_configs, self.transcript)
        self._emit("judge_verdict", verdict=asdict(verdict_b))
        judge_verdicts = [verdict_a, verdict_b]

        agreed = self._verdicts_agree(verdict_a, verdict_b)
        tie_break_triggered = False

        if not agreed:
            tie_break_triggered = True
            self._emit("tie_break_triggered", judge_a_reasoning=verdict_a.reasoning, judge_b_reasoning=verdict_b.reasoning)
            self._run_tie_break_round(verdict_a, verdict_b)
            verdict_a = self.judge_a.judge(self.topic, self.agent_configs, self.transcript)
            self._emit("judge_verdict", verdict=asdict(verdict_a))
            verdict_b = self.judge_b.judge(self.topic, self.agent_configs, self.transcript)
            self._emit("judge_verdict", verdict=asdict(verdict_b))
            judge_verdicts.extend([verdict_a, verdict_b])
            agreed = self._verdicts_agree(verdict_a, verdict_b)

        final_winner = verdict_a.winner if agreed else ""
        disagreement_rate = record_and_get_disagreement_rate(run_id, agreed)
        total_llm_calls = (
            sum(a.call_count for a in self.debaters)
            + (self.fact_checker.call_count if self.fact_checker else 0)
            + self.judge_a.call_count
            + self.judge_b.call_count
        )

        run = DebateRun(
            run_id=run_id,
            topic=self.topic,
            mode=self.mode,
            max_rounds=self.max_rounds,
            agents=self.agent_configs,
            transcript=self.transcript,
            judge_verdicts=judge_verdicts,
            claim_flags=self.claim_flags,
            dropped_agents=sorted(self.dropped_agents),
            judges_agreed=agreed,
            tie_break_triggered=tie_break_triggered,
            final_winner=final_winner,
            disagreement_rate=disagreement_rate,
            total_llm_calls=total_llm_calls,
            termination_reason="max_rounds_reached",
        )
        self._save(run)
        return run

    def _run_tie_break_round(self, verdict_a: JudgeVerdict, verdict_b: JudgeVerdict) -> None:
        tie_break_round = self.max_rounds + 1
        for agent in self._active_debaters():
            content = agent.tie_break_response(self.topic, list(self.transcript), verdict_a.reasoning, verdict_b.reasoning)
            self._append_statement(Statement(agent.config.agent_id, round=tie_break_round, phase="tie_break", content=content))

    @staticmethod
    def _verdicts_agree(verdict_a: JudgeVerdict, verdict_b: JudgeVerdict) -> bool:
        return bool(verdict_a.winner) and verdict_a.winner == verdict_b.winner

    def _active_debaters(self) -> list[DebateAgent]:
        return [a for a in self.debaters if a.config.agent_id not in self.dropped_agents]

    def _check_and_apply_repetition(self, agent: DebateAgent, statement: Statement) -> bool:
        """Returns True if the agent was dropped for repeating itself."""
        last_own = next(
            (s for s in reversed(self.transcript) if s.agent_id == agent.config.agent_id),
            None,
        )
        if last_own is None:
            return False

        is_repeating, score = self.repetition_detector.is_repeating(last_own.content, statement.content)
        if not is_repeating:
            return False

        self.dropped_agents.add(agent.config.agent_id)
        self._emit("agent_dropped", agent_id=agent.config.agent_id, round=statement.round, similarity=score)
        self._append_statement(
            Statement(
                agent.config.agent_id,
                round=statement.round,
                phase="dropped",
                content=f"Dropped from further rounds — statement similarity {score:.2f} >= threshold, repeating prior point.",
            )
        )
        return True

    def _format_pending_flags(self) -> str:
        if not self.claim_flags:
            return ""
        return "\n".join(f"- ({f.agent_id}) {f.claim} — {f.reason}" for f in self.claim_flags)

    def _append_statement(self, statement: Statement) -> None:
        self.transcript.append(statement)
        self._emit("statement", statement=asdict(statement))

    def _emit(self, event_type: str, **data) -> None:
        if self._on_event is not None:
            self._on_event({"type": event_type, **data})

    def _save(self, run: DebateRun) -> None:
        RUNS_DIR.mkdir(exist_ok=True)
        out_path = RUNS_DIR / f"{run.run_id}.json"
        out_path.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")
