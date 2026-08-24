# Walkthrough

Practical guide to running and using this project. For architecture rationale see
[multi-agent-debate-system-plan.md](multi-agent-debate-system-plan.md); for build
history and how to resume development see [CONTINUE.md](CONTINUE.md).

## 1. First-time setup

```bash
git clone https://github.com/kingtiwari2002/multi-agent-debate-system.git
cd multi-agent-debate-system

python -m venv .venv
.venv/Scripts/activate          # Windows. macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Edit `.env` and fill in both keys:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Both are required by default — the built-in agent presets ([src/presets.py](src/presets.py))
deliberately mix Claude and GPT-4o across debaters and judges to avoid correlated
blind spots. See [README.md#model-mix](README.md#model-mix) for why.

Build the frontend once (and again after any `web/frontend/src` change):

```bash
cd web/frontend
npm install
npm run build
cd ../..
```

## 2. Running the web UI

```bash
python web/backend/main.py
```

This serves both the API and the built React app on **http://localhost:55786** — a
single port, no separate frontend dev server needed.

### Starting a debate

1. Open `http://localhost:55786`.
2. On the "New debate" tab, enter a topic.
   - **Adversarial mode** wants a claim/decision, e.g. "Remote work improves
     productivity" — 2 agents will argue for it, 2 against, 1 fact-checks both sides.
   - **Ensemble mode** wants a question with a real answer, e.g. "What's the best
     approach to detect duplicate records in a 10M-row table?" — 5 agents solve it
     independently, then debate to converge on the best answer.
3. Set max rounds (default 3 — includes the opening and closing rounds, so 3 means 1
   rebuttal round in between).
4. Click "Start debate". You'll see each agent's column stream live: opening →
   rebuttal(s) → closing. A dropped agent (caught repeating itself) is grayed out.
   Fact-check flags appear in a panel above the columns as they're raised.
5. Once judgment finishes, a panel appears below showing Judge A's rubric scores and
   Judge B's strongest/weakest-unrefuted-point audit side by side, whether they
   agreed, and the final winner. If they initially disagreed, you'll also see the
   tie-break round's re-judgment.

### Browsing past debates

The "History" tab lists every run (topic, mode, winner, agreement, LLM call count).
Click any row to replay its full transcript and judgment panel — this reads straight
from the saved JSON in `runs/`, so it works even for runs from a previous session.

## 3. Running a debate from the CLI

Useful for scripting or when you don't want the UI running:

```bash
python main.py --topic "Remote work improves productivity" --mode adversarial --rounds 3
python main.py --topic "Best way to dedupe 10M rows" --mode ensemble --rounds 3
```

Prints the full transcript, fact-check flags, dropped agents, both judges' verdicts,
and the combined result to stdout. Also saves to `runs/<run_id>.json` exactly like the
web UI does — the two interfaces share the same orchestrator and storage.

## 4. Running the eval harness

This is the "is the extra cost of 5 agents + 2 judges actually earning its keep?"
check from the plan's Section 10. It runs the full debate system *and* a single-agent
baseline over a benchmark of known-answer questions, grades both, and reports the
accuracy delta:

```bash
python run_eval.py --mode ensemble --rounds 3
```

Default benchmark is [data/benchmark_questions.json](data/benchmark_questions.json)
(10 factual/reasoning questions with known answers). Point `--questions` at your own
file in the same `[{"question": ..., "answer": ...}, ...]` shape to eval something
else. Output includes:

- Debate system accuracy vs. single-agent baseline accuracy
- Judge agreement rate across the batch
- Average rounds-to-termination
- Per-question pass/fail table

A report is also saved to `runs/eval_reports/eval_<timestamp>.json`.

## 5. Reading the judge-agreement log

`runs/judge_agreement_log.jsonl` accumulates one line per debate ever run (`{run_id,
agreed}`), across every mode and every interface. `total_llm_calls` on each run and
the disagreement rate shown in the UI's judgment panel both derive from this kind of
bookkeeping — if you see the disagreement rate creep above 30%, the plan's Section 4
take is that the judge rubric is underspecified, not that the debates are genuinely
close.

## 6. Common issues

| Symptom | Fix |
|---|---|
| `KeyError: 'ANTHROPIC_API_KEY'` or similar on startup | `.env` isn't filled in, or you're running from a shell that didn't load it — check `.env` exists and both keys are set. |
| Web UI loads but shows old content after a frontend change | You edited `web/frontend/src` but didn't rebuild — run `npm run build` in `web/frontend`, no backend restart needed (it reads the built files fresh each request). |
| Port 55786 already in use | Something else is bound to it, or a previous `python web/backend/main.py` is still running — stop that process first. |
| A debate finishes with `final_winner` empty | Judges disagreed even after the tie-break round — check `judge_verdicts` in the run's JSON (or the UI's judgment panel) for both judges' reasoning; this is flagged for human review by design, not a bug. |
| An agent shows as "dropped" mid-debate | The repetition detector caught it repeating a prior statement almost verbatim — this is intentional (Section 5 of the plan), not an error. |
