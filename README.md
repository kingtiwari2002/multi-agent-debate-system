# Multi-Agent Debate System

5 independent LLM agents debate a topic (or independently solve a problem), and 2
independent judges score/synthesize the outcome. Two modes on the same architecture:

- **Adversarial mode** — 2 agents pro / 2 agents con / 1 neutral fact-checker,
  debating a claim or decision.
- **Ensemble mode** — 5 agents independently solve the same problem with different
  personas/temperatures, then debate each other's answers to converge on the best one
  (the "society of minds" / debate-for-accuracy pattern).

Two judges run independently (no cross-visibility) and their reasoning — not their
verdicts — feeds one capped tie-break round when they disagree. See
[`multi-agent-debate-system-plan.md`](multi-agent-debate-system-plan.md) for the full
original design rationale, or [WALKTHROUGH.md](WALKTHROUGH.md) for how to actually use
this, or [CONTINUE.md](CONTINUE.md) for current build status and how to resume
development.

## Architecture

```
src/
  adapters/        Provider-agnostic LLM interface (Anthropic + OpenAI implementations)
  agent.py         DebateAgent — independent history per agent, stance-locked
  judge.py         RubricJudge (Judge A) + AdversarialAuditorJudge (Judge B)
  fact_checker.py  Neutral 5th role, adversarial mode only
  repetition.py    Embedding-similarity repetition detector (drops agents that repeat)
  orchestrator.py  The state machine: rounds, judging, tie-break, event streaming
  presets.py       Default 5-agent rosters for adversarial/ensemble mode
  judge_stats.py   Cross-run judge agreement-rate tracking
  eval/            Eval harness: debate system vs. single-agent baseline
  models.py        Dataclasses: AgentConfig, Statement, ClaimFlag, JudgeVerdict, DebateRun

web/
  backend/         FastAPI app — REST + WebSocket, also serves the built frontend
  frontend/        React (Vite) app — live debate view, judge panel, run history

main.py            CLI: run a single debate
run_eval.py        CLI: run the eval harness against data/benchmark_questions.json
data/               Benchmark questions for eval
runs/               Per-debate JSON logs + eval reports (gitignored, created at runtime)
```

## Requirements

- Python 3.11+
- Node.js 18+ (for building the frontend)
- Anthropic API key, OpenAI API key (both used — see [Model mix](#model-mix))

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

cp .env.example .env          # then fill in ANTHROPIC_API_KEY and OPENAI_API_KEY

cd web/frontend
npm install
npm run build                 # produces web/frontend/dist, served by the backend
cd ../..
```

## Running it

**Web UI (API + frontend on one port, 55786):**

```bash
python web/backend/main.py
```

Open `http://localhost:55786`. Start a debate from the "New debate" tab, watch it
stream live, then browse past runs in "History".

> The frontend is a static build — after changing anything under `web/frontend/src`,
> re-run `npm run build` there before the backend will serve the update.

**CLI, single debate:**

```bash
python main.py --topic "Remote work improves productivity" --mode adversarial --rounds 3
```

**CLI, eval harness (debate system vs. single-agent baseline):**

```bash
python run_eval.py --mode ensemble --rounds 3
```

## Model mix

Both an Anthropic and an OpenAI key are required because the default presets
deliberately mix providers — 4 agents on Claude with distinct personas + 1 on GPT-4o —
to avoid correlated blind spots, and Judge B defaults to a different model family than
Judge A to reduce self-preference bias. This is a first-build default, not a hard
requirement of the architecture; see [CONTINUE.md](CONTINUE.md) for the planned
per-agent model config panel (Phase 5e, not yet built) that will make this
user-configurable instead of hardcoded in `src/presets.py`.

## Optional: routing through AgentRouter

[AgentRouter](https://agentrouter.org) is an optional third-party routing layer that
can sit in front of a call instead of hitting Anthropic/OpenAI directly — it is **not**
a replacement for the `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` setup above, which keeps
working exactly as-is whether or not AgentRouter is configured. To use it for a
particular agent, judge, or fact-checker slot, set `AGENTROUTER_API_KEY` in `.env` and
set that slot's `provider` to `agentrouter` (OpenAI-compatible endpoint) or
`agentrouter_anthropic` (Anthropic-compatible endpoint) — the `model` field stays
whatever you'd normally pass (`gpt-4o`, `claude-sonnet-5`, etc.), since AgentRouter
routes by model name. Nothing changes for any slot left on `anthropic`/`openai`.

## Status

Phases 1–5d of the build plan are complete (core loop, 5 agents + fact-checker +
repetition detector, 2 judges + tie-break, eval harness, web UI with live view /
judgment panel / history / polish). Phase 5e (config/admin panel for per-agent model
selection) is the next planned step. Full detail in [CONTINUE.md](CONTINUE.md).
