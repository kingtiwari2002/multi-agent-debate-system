from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class AgentConfig:
    agent_id: str
    persona: str
    position: str
    provider: str = "anthropic"
    model: str = "claude-sonnet-5"
    temperature: float = 0.7
    role: str = "debater"  # "debater" | "fact_checker"


@dataclass
class Statement:
    agent_id: str
    round: int
    phase: str  # "opening" | "rebuttal" | "closing" | "dropped"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ClaimFlag:
    agent_id: str
    round: int
    claim: str
    reason: str


@dataclass
class JudgeVerdict:
    judge_id: str
    scores: dict
    winner: str
    reasoning: str


@dataclass
class DebateRun:
    run_id: str
    topic: str
    mode: str
    max_rounds: int
    agents: list
    transcript: list
    judge_verdicts: list
    claim_flags: list = field(default_factory=list)
    dropped_agents: list = field(default_factory=list)
    judges_agreed: bool = None
    tie_break_triggered: bool = False
    final_winner: str = ""
    disagreement_rate: float = 0.0
    total_llm_calls: int = 0
    termination_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "topic": self.topic,
            "mode": self.mode,
            "max_rounds": self.max_rounds,
            "agents": [asdict(a) for a in self.agents],
            "transcript": [asdict(s) for s in self.transcript],
            "judge_verdicts": [asdict(v) for v in self.judge_verdicts],
            "claim_flags": [asdict(f) for f in self.claim_flags],
            "dropped_agents": self.dropped_agents,
            "judges_agreed": self.judges_agreed,
            "tie_break_triggered": self.tie_break_triggered,
            "final_winner": self.final_winner,
            "disagreement_rate": self.disagreement_rate,
            "total_llm_calls": self.total_llm_calls,
            "termination_reason": self.termination_reason,
            "created_at": self.created_at,
        }
