import argparse
import json

from dotenv import load_dotenv

from src.eval.harness import run_benchmark

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the eval harness: debate system vs. single-agent baseline.")
    parser.add_argument("--questions", default="data/benchmark_questions.json", help="Path to a JSON list of {question, answer}.")
    parser.add_argument("--mode", choices=["adversarial", "ensemble"], default="ensemble", help="Ensemble mode is the intended fit for known-answer benchmarks.")
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()

    questions = json.loads(open(args.questions, encoding="utf-8").read())
    summary = run_benchmark(questions, mode=args.mode, max_rounds=args.rounds)

    print(f"\n=== Eval summary ({summary['n_questions']} questions, mode={summary['mode']}) ===")
    print(f"Debate system accuracy:   {summary['debate_accuracy']:.0%}")
    print(f"Single-agent baseline:    {summary['baseline_accuracy']:.0%}")
    print(f"Judge agreement rate:     {summary['judge_agreement_rate']:.0%}")
    print(f"Avg rounds to terminate:  {summary['avg_rounds_to_termination']:.1f}")

    delta = summary["debate_accuracy"] - summary["baseline_accuracy"]
    if delta > 0:
        print(f"\nDebate system beat the baseline by {delta:.0%}.")
    elif delta < 0:
        print(f"\nDebate system UNDERPERFORMED the baseline by {-delta:.0%} — the extra cost isn't earning its keep on this benchmark.")
    else:
        print("\nDebate system matched the baseline exactly — no accuracy gain on this benchmark.")

    print("\n--- per-question results ---")
    for r in summary["results"]:
        mark_debate = "PASS" if r["debate_correct"] else "FAIL"
        mark_base = "PASS" if r["baseline_correct"] else "FAIL"
        print(f"[debate {mark_debate} | baseline {mark_base}] {r['question']} (expected: {r['correct_answer']})")


if __name__ == "__main__":
    main()
