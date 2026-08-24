# Continuing this project

Status snapshot and build history so this can be picked up in a fresh session (or by
someone else) with no lost context. If you're an AI assistant resuming this: read this
file, [README.md](README.md), and [multi-agent-debate-system-plan.md](multi-agent-debate-system-plan.md)
(the original design doc) before making changes.

## Status

| Phase | What | Status |
|---|---|---|
| 1 | Core loop: 2 agents + 1 judge, provider-agnostic adapter layer | Done |
| 2 | Scale to 5 agents, fact-checker role, repetition detector | Done |
| 3 | Second judge, agreement/disagreement, tie-break round | Done |
| 4 | Eval harness: debate system vs. single-agent baseline | Done |
| 5a | Backend API (FastAPI, REST + WebSocket streaming) | Done |
| 5b | Frontend: live debate view (per-agent columns) | Done |
| 5c | Frontend: judgment panel + history/replay view | Done |
| 5d | Polish: call-count display, loading/error states, responsive layout | Done |
| 5e | Config/admin panel — per-agent model picker with default preset | **Not started — next step** |

Everything through 5d has been exercised end-to-end with stubbed LLM adapters (see
[Verification approach](#verification-approach-used-so-far) below) — but **no run has
been done yet against real API keys**. Do that before trusting cost/latency
assumptions or shipping this anywhere.

## How to resume

Tell whoever/whatever picks this up next: *"Read CONTINUE.md, then proceed with Phase
5e"* — that's enough context to continue without re-deriving the architecture. If the
direction has changed since this was written, update the status table above first.

## Key decisions worth knowing (not obvious from reading the code alone)

- **Provider-agnostic adapter layer built in Phase 1, not retrofitted later.** When
  asked whether the multi-LLM config panel should be early or late work, the explicit
  choice was: build the `src/adapters/` abstraction (Claude + OpenAI) from Phase 1
  onward so agent/judge code never assumes a single provider, but defer the actual
  config *UI* to Phase 5e. This is why `AgentConfig` has had `provider`/`model` fields
  since the very first commit-equivalent.
- **Default presets deliberately mix providers.** `src/presets.py`: 4 debaters on
  Claude with varied personas/temperature + 1 on GPT-4o; Judge A defaults to Claude,
  Judge B defaults to GPT-4o. This isn't arbitrary — it's the plan's Section 3/4
  "avoid correlated blind spots" and "keep judges model-distinct from debaters"
  guidance, made concrete. Phase 5e's job is to make this user-configurable instead of
  hardcoded, with this mix as the default preset and a reset-to-default button.
- **Fact-checker runs on `claude-haiku-4-5` by default** — cheaper model, since
  flagging unsupported claims is a simpler task than open debate (plan Section 9 cost
  guidance).
- **Repetition detector** (`src/repetition.py`) uses OpenAI embeddings + cosine
  similarity when `OPENAI_API_KEY` is set, falls back to `difflib.SequenceMatcher` text
  ratio otherwise. Threshold is 0.92. An agent that trips it gets a `"dropped"` phase
  statement appended and is excluded from all later rounds, including closing.
- **Tie-break logic feeds judges' *reasoning*, not verdicts**, back to debaters
  (plan Section 4 explicit requirement — avoids the debaters just being told "you
  lost, argue harder"). Capped at exactly 1 retry regardless of outcome.
- **`final_winner` is deliberately left empty** when judges still disagree after the
  tie-break — this is surfaced in the UI as "unresolved — flag for human review", not
  silently defaulted to either judge's pick.
- **Eval harness grades with an LLM, not substring matching** (`src/eval/grader.py`) —
  more robust to phrasing differences on reasoning questions, at the cost of one extra
  cheap-model call per question per side.
- **Web UI consolidated to one port (55786).** Originally built with a separate Vite
  dev server on 5173 talking to the API via CORS; later collapsed so
  `web/backend/main.py` mounts the *built* `web/frontend/dist` via `StaticFiles`,
  registered after all `/api/*` and `/ws/*` routes so those still take priority. This
  means **the frontend has no hot-reload in this setup** — after editing anything
  under `web/frontend/src`, you must `npm run build` again before the backend serves
  the change. `web/frontend/src/api.js` uses `window.location.origin` for its API
  base, so this only works when frontend and backend are same-origin (i.e., always, in
  this setup).
- **Total LLM call count is tracked and shown**, not a dollar cost — a per-model
  pricing table would go stale and wasn't worth the maintenance burden. `call_count` is
  incremented on every `DebateAgent`/`RubricJudge`/`AdversarialAuditorJudge`/
  `FactCheckerAgent` instance and summed into `DebateRun.total_llm_calls`.

## Known gaps vs. the original plan

The plan (Section 5) describes two termination/scoring behaviors not yet built:

- **No convergence early-stop.** Only fixed max-rounds and repetition-based
  individual-agent drops exist. The plan's "if Judge A's per-round scores stop
  changing, stop early" isn't implemented.
- **No per-round Judge A scoring.** Judge A currently only scores once, at the very
  end of the full transcript — not after each rebuttal round as Section 5 describes.
  This was a deliberate scope call (build-phases list in Section 8 doesn't mention
  per-round scoring until the full judging phase), but it's worth flagging if someone
  expects live per-round scores in the UI.

Neither blocks Phase 5e. Both are reasonable candidates for a Phase 6 if the eval
harness (Phase 4) results suggest agents are burning rounds without converging —
check `avg_rounds_to_termination` from `python run_eval.py` first before building
either.

## What Phase 5e should include

From the original scoping discussion:

- Per-agent (and per-judge) row: model dropdown + temperature/persona field, for all 5
  agent slots + 2 judge slots.
- "Reset to default" button — reloads the `src/presets.py` roster described above,
  discarding custom picks.
- Persist the active config alongside each run's JSON log (already structurally easy —
  `DebateRun.agents` already stores full `AgentConfig` including provider/model per
  run) so past runs stay reproducible even after the panel's settings change later.
- Backend: a way to accept a custom agent roster in `POST /api/debates` instead of
  always calling `build_agents(mode)` from `src/presets.py` — the orchestrator and
  `AgentConfig` already support this, `web/backend/main.py`'s `StartDebateRequest`
  does not yet.

## Verification approach used so far

No automated test suite exists yet. Every phase was verified by writing a throwaway
`scratch_test_*.py` or `scratch_stub_backend.py` script at the project root that
monkeypatches `src.adapters.build_adapter` (and the modules that imported it directly)
with a stub returning deterministic text, so the full orchestrator/API/UI flow could
be exercised without real API calls or cost. These scripts were always deleted after
use — none are committed. If continuing, consider formalizing the more useful ones
(especially the orchestrator repetition/tie-break logic tests) into a real
`tests/` directory with pytest, since re-deriving them from scratch each time is
wasted effort.

One thing to watch if you write a new stub: give each simulated statement genuinely
different text between calls. A stub that returns near-identical strings (e.g. just
an incrementing call counter appended to otherwise fixed text) will trip the real
repetition detector and drop agents unintentionally — this happened twice during
development and both times turned out to be a test-fixture artifact, not an
orchestrator bug.

## File map

```
src/adapters/         LLMAdapter interface + Anthropic/OpenAI implementations
src/agent.py           DebateAgent: opening/rebuttal/closing/tie_break_response
src/judge.py           RubricJudge (Judge A), AdversarialAuditorJudge (Judge B)
src/fact_checker.py    FactCheckerAgent
src/repetition.py      RepetitionDetector
src/orchestrator.py    DebateOrchestrator — the state machine, on_event streaming hook
src/presets.py         build_adversarial_agents / build_ensemble_agents / build_agents
src/judge_stats.py     Cross-run disagreement-rate log (runs/judge_agreement_log.jsonl)
src/models.py          AgentConfig, Statement, ClaimFlag, JudgeVerdict, DebateRun
src/eval/               baseline.py, grader.py, harness.py — eval harness

web/backend/main.py         FastAPI app: /api/debates, /ws/debates/{id}, static mount
web/backend/run_manager.py  Thread + queue bridge between orchestrator and WebSocket

web/frontend/src/api.js               REST + WebSocket client (same-origin)
web/frontend/src/App.jsx              Tab shell (New debate / History)
web/frontend/src/views/               LiveDebateView, HistoryView
web/frontend/src/components/          DebateForm, AgentColumn, FactCheckPanel,
                                       StatusBanner, JudgePanel, HistoryTable, ReplayView

main.py          CLI: single debate
run_eval.py      CLI: eval harness
data/benchmark_questions.json   Default eval benchmark (ensemble mode)
.claude/launch.json             Preview-server config (debate-backend, port 55786)
```
