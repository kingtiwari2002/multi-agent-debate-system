import argparse

from dotenv import load_dotenv

from src.orchestrator import DebateOrchestrator
from src.presets import build_agents

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a debate (5 agents + 1 judge).")
    parser.add_argument("--topic", required=True, help="The resolution/claim/problem to debate.")
    parser.add_argument("--rounds", type=int, default=3, help="Max rounds including opening and closing.")
    parser.add_argument("--mode", choices=["adversarial", "ensemble"], default="adversarial")
    args = parser.parse_args()

    agent_configs = build_agents(args.mode)
    orchestrator = DebateOrchestrator(topic=args.topic, agent_configs=agent_configs, max_rounds=args.rounds, mode=args.mode)
    run = orchestrator.run()

    print(f"\n=== Debate run {run.run_id} saved ===\n")
    for statement in run.transcript:
        print(f"[R{statement.round} {statement.phase}] {statement.agent_id}: {statement.content}\n")

    if run.claim_flags:
        print("--- fact-check flags ---")
        for flag in run.claim_flags:
            print(f"[R{flag.round}] {flag.agent_id}: {flag.claim} — {flag.reason}")
        print()

    if run.dropped_agents:
        print(f"--- dropped for repetition: {', '.join(run.dropped_agents)} ---\n")

    for verdict in run.judge_verdicts:
        print(f"--- {verdict.judge_id} verdict ---")
        print(f"Winner: {verdict.winner}")
        print(f"Reasoning: {verdict.reasoning}")
        print(f"Scores: {verdict.scores}")
        print()

    print(f"--- combined result ---")
    print(f"Judges agreed: {run.judges_agreed}")
    print(f"Tie-break triggered: {run.tie_break_triggered}")
    print(f"Final winner: {run.final_winner or '(unresolved — flag for human review)'}")
    print(f"All-time judge disagreement rate: {run.disagreement_rate:.0%}")
    if run.disagreement_rate > 0.30:
        print("WARNING: disagreement rate above 30% — rubric is likely underspecified, not that debates are close.")


if __name__ == "__main__":
    main()
