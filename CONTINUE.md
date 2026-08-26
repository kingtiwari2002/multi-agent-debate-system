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
| 5e | Config/admin panel — per-agent model picker with default preset | Done |
| 5f | Provider support — Gemini + NVIDIA NIM adapters | Done |
| 5g | Real per-call latency + $ cost tracking (all 4 providers) | Done — **not yet run against real keys** |

Everything through 5g has been exercised end-to-end with a stubbed LLM adapter (see
[Verification approach](#verification-approach-used-so-far) below) — but **no run has
been done yet against real API keys**. The stub fabricates plausible token counts and
latencies to prove the plumbing works; it says nothing about real model quality, real
latency, or whether the Phase 5g pricing table is still accurate. Do that run before
trusting any of the three for real.

## How to resume

Phase 5g is done but unverified against real keys — **that's the very next step**, not
a new phase: run a debate with real `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/
`GEMINI_API_KEY`/`NVIDIA_API_KEY` and sanity-check the reported cost against each
provider's own usage dashboard once. After that, Phase 6 candidates are under
[Known gaps vs. the original plan](#known-gaps-vs-the-original-plan) — check
`avg_rounds_to_termination` from `python run_eval.py` against real API keys first to
see whether they're actually worth building. If the direction has changed since this
was written, update the status table above first.

### Phase 5g implementation notes

- **`LLMAdapter.generate()` now returns a `GenerationResult`** (`src/adapters/base.py`:
  `text`, `input_tokens`, `output_tokens`, `latency_seconds`) instead of a bare string —
  a real signature change all four adapters and every caller (`DebateAgent`,
  `RubricJudge`, `AdversarialAuditorJudge`, `FactCheckerAgent`) had to follow. Latency is
  measured with `time.perf_counter()` wrapped tightly around the actual SDK call in each
  adapter (excludes prompt-building overhead, includes real network + inference time).
  Token counts come from each provider's own response — `response.usage` (Anthropic),
  `response.usage.prompt_tokens`/`completion_tokens` (OpenAI-shaped: OpenAI itself and
  NVIDIA NIM, which reuses the same client), `response.usage_metadata.prompt_token_count`/
  `candidates_token_count` (Gemini) — never estimated from a local tokenizer.
- **`src/pricing.py`** is a `(provider, model) -> ($/1M input, $/1M output)` table plus
  `estimate_cost_usd(...)`, which returns `None` — not a fallback rate — for any
  model not in the table. This matters: unpriced calls show as "cost unknown" in the
  UI, never as a silently wrong dollar figure. Anthropic's rates came from the
  `claude-api` skill (authoritative); OpenAI/Gemini/NVIDIA NIM rates came from
  third-party pricing aggregators (WebSearch, no official API), since this skill has no
  equivalent authoritative source for those three — re-verify before trusting them
  beyond rough budgeting, and expect these to go stale — `gemini-2.0-flash` was
  already retired mid-search while building this table, and is deliberately left
  unpriced rather than carrying a rate for a model that no longer serves traffic.
- **`Statement` and `JudgeVerdict`** (`src/models.py`) each gained `latency_seconds`,
  `input_tokens`, `output_tokens`, `cost_usd` — populated per-call in `orchestrator.py`
  (statements, via a new `_build_statement` helper) and inside `judge.py` (verdicts,
  since judges construct their own return value). `FactCheckerAgent` has no per-call
  record to attach metrics to, so it accumulates its own running totals instead
  (`total_input_tokens`/etc. on the instance), summed into `DebateRun` alongside
  everything else. `DebateRun` gained `total_input_tokens`, `total_output_tokens`,
  `total_latency_seconds`, `total_cost_usd`, and `unpriced_calls` (count of calls whose
  model had no pricing entry, so the UI can show "~$0.0198 (3 calls unpriced)" instead
  of quietly under-reporting).
- **Repetition-drop bookkeeping bug caught during this work and fixed**: when
  `_check_and_apply_repetition` discards a rebuttal statement for repeating the agent's
  prior point, the underlying LLM call still genuinely happened (real tokens, real
  latency, real cost) — only its text is thrown away. The first version of this feature
  zeroed those fields on the synthetic "dropped" statement that replaces it, silently
  under-counting the run's real cost. Fixed by carrying the discarded statement's real
  `latency_seconds`/`input_tokens`/`output_tokens`/`cost_usd` onto the "dropped" one
  instead of defaulting them — verified with a targeted stub test that forces a
  repetition (see verification section below).
- **Frontend**: `web/frontend/src/format.js` (`formatCost`/`formatLatency`) is shared by
  `AgentColumn` (per-statement badge), `JudgePanel` (per-verdict), and `StatusBanner`/
  `ReplayView` (run-level totals + unpriced-call count). `formatCost(null)` renders
  "cost unknown", never `$0.0000` or an omitted figure — the distinction matters since a
  real free/zero-cost call should look different from an un-priced one.
- NVIDIA NIM's curated model dropdown (`ConfigPanel.jsx`) leads with the two models that
  actually have a pricing entry (`nvidia/llama-3.1-nemotron-super-49b-v1`,
  `nvidia/nemotron-nano-9b-v2`); the earlier `meta/llama-3.1-*` placeholders are still
  selectable but show "cost unknown" until someone adds verified rates for them to
  `src/pricing.py`.

### Phase 5e implementation notes

- `web/backend/main.py`'s `StartDebateRequest` now accepts optional `agents` (full
  `AgentConfig` roster), `judge_a`, and `judge_b` overrides; omitting them falls back
  to `build_agents(mode)` and the hardcoded judge defaults exactly as before.
- New `GET /api/presets/{mode}` returns the default roster + judge config as JSON so
  the frontend never hardcodes the preset values — it's the same source of truth the
  "Reset to default" button re-fetches from.
- `DebateOrchestrator` takes `judge_a_provider`/`judge_a_model`/`judge_b_provider`/
  `judge_b_model` (all defaulted to the original hardcoded values), and `DebateRun`
  now persists `judge_a_config`/`judge_b_config` alongside `agents` so past runs stay
  fully reproducible, judges included — `JudgePanel` reads this back to show each
  judge's model in its card label.
- Frontend: `ConfigPanel.jsx` is a collapsed-by-default panel with one row per agent
  slot (provider/model dropdowns, persona text, temperature) plus one row per judge
  (provider/model only). `LiveDebateView` owns `mode`/`agents`/`judgeA`/`judgeB` state,
  fetches presets on mode change, and threads the (possibly edited) roster through
  `startDebate`.
- Verified end-to-end with a stubbed adapter (custom roster override, judge-config
  override, the `at least one debater is required` validation path, and the full
  WebSocket statement stream) plus a real browser run against the built frontend —
  screenshots showed the config panel, per-agent opinion text, and judge cards with
  model names all rendering correctly. No test files were committed (same throwaway
  convention as every other phase — see below).

### Phase 5f implementation notes

- Two new adapters in `src/adapters/`: `GeminiAdapter` (Google's unified `google-genai`
  SDK, `genai.Client(api_key=...).models.generate_content(...)`, reads
  `GEMINI_API_KEY`) and `NvidiaNimAdapter` (reuses the `openai` client pointed at
  NVIDIA's OpenAI-compatible endpoint `https://integrate.api.nvidia.com/v1`, reads
  `NVIDIA_API_KEY` — no new SDK dependency needed for NIM itself).
  Both registered in `src/adapters/__init__.py`'s `_REGISTRY` under `"gemini"` and
  `"nvidia_nim"`.
- `requirements.txt` gained `google-genai`; `.env.example` gained `GEMINI_API_KEY` and
  `NVIDIA_API_KEY`.
- Frontend `ConfigPanel.jsx`: provider dropdowns (agents and judges) now list all four
  providers, each with its own curated model list. No backend validation was added
  beyond what already existed for anthropic/openai — an unrecognized `provider` string
  still surfaces as a run-time error event exactly as before, symmetric across all four.
- `src/presets.py`'s default roster is untouched (still the Claude-heavy + one-GPT-4o
  mix from Phase 1) — Gemini/NIM are opt-in via the config panel or a custom roster
  payload, not part of the default preset. Revisit if there's a reason to rebalance the
  default mix now that more providers exist.
- Verified with the same stub-adapter approach: a roster mixing all four providers
  (including judges on Gemini and NIM) ran end-to-end through the orchestrator and
  WebSocket stream, and a browser screenshot confirmed both new providers appear and
  swap their model lists correctly in the config panel.

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

## What Phase 5e included

From the original scoping discussion (all now built — see "Phase 5e implementation
notes" above for how):

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
src/adapters/         LLMAdapter interface + Anthropic/OpenAI/Gemini/NVIDIA NIM implementations
src/agent.py           DebateAgent: opening/rebuttal/closing/tie_break_response
src/judge.py           RubricJudge (Judge A), AdversarialAuditorJudge (Judge B)
src/fact_checker.py    FactCheckerAgent
src/repetition.py      RepetitionDetector
src/orchestrator.py    DebateOrchestrator — the state machine, on_event streaming hook
src/presets.py         build_adversarial_agents / build_ensemble_agents / build_agents
src/judge_stats.py     Cross-run disagreement-rate log (runs/judge_agreement_log.jsonl)
src/models.py          AgentConfig, Statement, ClaimFlag, JudgeVerdict, DebateRun
src/pricing.py         $/1M-token rates + estimate_cost_usd — returns None when unpriced
src/eval/               baseline.py, grader.py, harness.py — eval harness

web/backend/main.py         FastAPI app: /api/debates, /ws/debates/{id}, static mount
web/backend/run_manager.py  Thread + queue bridge between orchestrator and WebSocket

web/frontend/src/api.js               REST + WebSocket client (same-origin)
web/frontend/src/App.jsx              Tab shell (New debate / History)
web/frontend/src/views/               LiveDebateView, HistoryView
web/frontend/src/components/          DebateForm, AgentColumn, FactCheckPanel,
                                       StatusBanner, JudgePanel, HistoryTable, ReplayView,
                                       ConfigPanel
web/frontend/src/format.js            formatCost / formatLatency — shared by the above

main.py          CLI: single debate
run_eval.py      CLI: eval harness
data/benchmark_questions.json   Default eval benchmark (ensemble mode)
.claude/launch.json             Preview-server config (debate-backend, port 55786)
```
