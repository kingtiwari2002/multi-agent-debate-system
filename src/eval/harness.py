import json
from pathlib import Path

from ..models import DebateRun
from ..orchestrator import DebateOrchestrator
from ..presets import build_agents
from .baseline import SingleAgentBaseline
from .grader import AnswerGrader

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "runs" / "eval_reports"


def _winning_statement(run: DebateRun) -> str:
    winner_id = run.final_winner or (run.judge_verdicts[0].winner if run.judge_verdicts else "")
    if not winner_id:
        return ""
    for statement in reversed(run.transcript):
        if statement.agent_id == winner_id and statement.phase in ("closing", "tie_break"):
            return statement.content
    return ""


def _rounds_to_termination(run: DebateRun) -> int:
    return max((s.round for s in run.transcript), default=0)


def run_benchmark(questions: list[dict], mode: str = "ensemble", max_rounds: int = 3) -> dict:
    """Runs the full debate system and a single-agent baseline over each
    question, grades both against the known correct answer, and reports the
    accuracy delta plus judge-agreement / rounds-to-termination stats — the
    numbers that answer 'is the extra cost of 5 agents + 2 judges earning its
    keep?' (Section 10 of the plan)."""
    grader = AnswerGrader()
    baseline = SingleAgentBaseline()
    results = []

    for item in questions:
        question, correct_answer = item["question"], item["answer"]

        agent_configs = build_agents(mode)
        run = DebateOrchestrator(topic=question, agent_configs=agent_configs, max_rounds=max_rounds, mode=mode).run()
        debate_text = _winning_statement(run)
        debate_correct = grader.is_correct(question, correct_answer, debate_text)

        baseline_text = baseline.answer(question)
        baseline_correct = grader.is_correct(question, correct_answer, baseline_text)

        results.append(
            {
                "question": question,
                "correct_answer": correct_answer,
                "run_id": run.run_id,
                "debate_winner": run.final_winner,
                "debate_correct": debate_correct,
                "baseline_correct": baseline_correct,
                "judges_agreed": run.judges_agreed,
                "tie_break_triggered": run.tie_break_triggered,
                "rounds_to_termination": _rounds_to_termination(run),
            }
        )

    n = len(results) or 1
    summary = {
        "mode": mode,
        "n_questions": len(results),
        "debate_accuracy": sum(r["debate_correct"] for r in results) / n,
        "baseline_accuracy": sum(r["baseline_correct"] for r in results) / n,
        "judge_agreement_rate": sum(r["judges_agreed"] for r in results) / n,
        "avg_rounds_to_termination": sum(r["rounds_to_termination"] for r in results) / n,
        "results": results,
    }
    _save(summary)
    return summary


def _save(summary: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = REPORTS_DIR / f"eval_{stamp}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
