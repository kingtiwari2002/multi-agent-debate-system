import json
from pathlib import Path

STATS_PATH = Path(__file__).resolve().parent.parent / "runs" / "judge_agreement_log.jsonl"


def record_and_get_disagreement_rate(run_id: str, agreed: bool) -> float:
    """Appends this run's agreement outcome to the running log and returns the
    all-time disagreement rate. A rate above 0.30 usually means the rubric is
    underspecified, not that the debates are genuinely close (Section 4)."""
    STATS_PATH.parent.mkdir(exist_ok=True)
    with STATS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"run_id": run_id, "agreed": agreed}) + "\n")

    records = STATS_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not records:
        return 0.0
    disagreements = sum(1 for line in records if not json.loads(line)["agreed"])
    return disagreements / len(records)
