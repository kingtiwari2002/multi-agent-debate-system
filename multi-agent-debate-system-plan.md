# Multi-Agent Debate System — Detailed Plan
### Architecture: 5 debating agents + 2 judges

---

## 1. What we're building

A system where **5 LLM agents** independently argue toward a resolution — either
assigned opposing/varied stances on a topic, or all attacking the same problem from
different reasoning angles — across structured rounds, with **2 independent judges**
scoring/synthesizing the outcome instead of one.

Two usable modes (pick per-run, same architecture supports both):

- **Adversarial mode**: 5 agents split across positions (e.g. 2-for, 2-against, 1
  neutral/moderator-of-facts) debating a claim or decision.
- **Ensemble reasoning mode**: 5 agents independently solve the same problem with
  different personas/temperatures/prompting strategies, then debate each other's
  answers to converge on the best one (this is the pattern used in "society of minds"
  / debate-for-accuracy research — it reliably improves factual accuracy over a
  single model call).

---

## 2. Why this design

**Why 5 agents (not 2–3)?**
- Odd number avoids permanent 2-2 deadlock dynamics.
- 5 gives enough diversity of reasoning paths for ensemble mode to have a real
  "majority signal" before judges even weigh in, while staying cheap enough to run
  every round (cost scales linearly with agent count, and 5× round-robin rounds is
  still tractable).
- Below 4, debates tend to just be one-on-one with observers; 5 creates actual
  coalition/counter-argument dynamics, which is where debate-for-accuracy gains come
  from.

**Why 2 judges (not 1)?**
- A single judge has **self-preference bias** if it shares a model family with any
  debater, and has no check on idiosyncratic scoring.
- Two judges, ideally on **different model families**, let you:
  - Cross-check verdicts — if both agree, high confidence; if they disagree, that
    disagreement is itself signal (flag for human review or trigger a tie-break round).
  - Average/ensemble their scores instead of trusting one rubric run.
- This mirrors inter-rater reliability practice in human evaluation — one rater is
  noise, two is a measurement.

---

## 3. Agent design

Each of the 5 agents is a fully independent conversational thread — **not** a shared
chat everyone sees identically. This matters: if all agents share one growing
transcript with identical framing, they converge/agree too fast (sycophancy
collapse). Instead:

| Component | Detail |
|---|---|
| **Persona/system prompt** | Distinct voice + explicit stance-lock instruction: *"You are Agent X, assigned to argue [position]. You must not concede or soften your position unless directly refuted by a specific factual claim."* |
| **Own history view** | Each agent sees: its own past statements + the public transcript of others' statements (not their internal reasoning/scratchpad) |
| **Model choice** | Doesn't have to be 5 different models — but at least varying temperature/persona is required for diversity. Best practice: 3-4 agents on one strong model with distinct personas, 1 on a different model family entirely, to avoid correlated blind spots |
| **Role assignment** | For adversarial mode: 2 pro / 2 con / 1 fact-checker-neutral. For ensemble mode: 5 independent solvers, roles emerge only in the rebuttal phase |

**Fact-checker/neutral 5th agent (adversarial mode)**: doesn't argue a side — its job
is to flag unsupported claims from either side each round. This one addition
significantly reduces "confident-sounding but wrong" arguments winning purely on
rhetoric.

---

## 4. Judge design

**Two judges, separate from all 5 debaters**, each running independently — they must
not see each other's verdict before submitting their own (avoid anchoring).

| Judge | Role |
|---|---|
| **Judge A — Rubric scorer** | Scores each agent/round against a fixed rubric: factual accuracy, logical validity, responsiveness to opponent's strongest point, and clarity. Outputs numeric scores, not just a winner. |
| **Judge B — Adversarial auditor** | Doesn't score rounds; specifically hunts for the single weakest unrefuted point and the single strongest unrefuted point across the whole debate, then gives a verdict based on which side has more unresolved weaknesses. Different lens = catches different failures than Judge A. |

**Combining verdicts:**
- If A and B agree on a winner/answer → return it with high confidence.
- If they disagree → don't average blindly. Trigger a **tie-break round**: feed both
  judges' reasoning (not verdicts) back to the debaters for one more rebuttal round,
  then re-judge. Cap at 1 tie-break to bound cost.
- Log disagreement rate over time — a system where judges disagree >30% of the time
  usually means the rubric is underspecified, not that the debates are close.

---

## 5. Debate protocol (concrete round structure)

```
Round 0 — Opening statements
  All 5 agents state their position/answer independently, no cross-visibility.

Round 1..N — Rebuttal rounds (round-robin order, randomized each run to avoid
  first-mover advantage)
  Each agent sees the full public transcript so far, responds to the strongest
  opposing point specifically (prompted to quote/reference it).

  After each round: Judge A scores that round. Fact-checker agent (if adversarial
  mode) flags any unsupported claims made in that round — flagged claims must be
  either substantiated or withdrawn in the next round.

Round N (final) — Closing statements
  Each agent gives a final position, explicitly addressing any claims that were
  flagged as unsupported and never resolved.

Judgment phase
  Judge A: final rubric scores.
  Judge B: adversarial audit verdict.
  Combine per Section 4.
```

**Termination conditions** (whichever hits first):
- Fixed max rounds (recommend N=3 rebuttal rounds as default — enough for real
  back-and-forth, cheap enough to run routinely)
- **Convergence early-stop**: if Judge A's per-round scores stop changing
  (agents are repeating themselves), stop early
- **Repetition detector**: simple embedding-similarity check between an agent's
  current statement and its own last statement — if too similar, force it to either
  concede a specific point or the orchestrator drops it from further rounds

---

## 6. Data flow / what each component sees

| Component | Sees |
|---|---|
| Agent (mid-debate) | Its own prior statements + full public transcript. NOT other agents' internal reasoning, NOT judge scores until the end. |
| Fact-checker agent | Same as above, plus explicit instruction to output structured claim-flags |
| Judge A / Judge B | Full public transcript only, after debate ends. No visibility into each other. |
| Orchestrator | Everything — manages turn order, injects fact-flags into next round's prompts, checks termination conditions, combines judge verdicts |

---

## 7. Tech stack (recommended for first build)

| Layer | Choice | Why |
|---|---|---|
| Orchestration | Plain Python state machine (not a heavy framework initially) | 5 agents × few rounds is simple enough that LangGraph/AutoGen adds overhead without much benefit until you need branching/parallelism you don't have yet |
| Agent calls | Anthropic API, `messages` endpoint, one persistent message list per agent | Straightforward, matches the "independent history per agent" requirement directly |
| Model mix | e.g. 4 agents on Claude (varied personas/temperature) + judges on a separate model, OR all-Claude with heavy persona differentiation if single-provider is a constraint | Reduces correlated-blind-spot risk on judges specifically |
| State storage | JSON per debate run (agents' full histories, judge verdicts, flags) | Enables replay/audit — useful for tuning rubrics later |
| Interface | Start CLI/notebook; add a simple live-transcript UI once the core loop is solid | Don't build UI before the debate logic is validated |

---

## 8. Build phases

1. **Phase 1 — Core loop, 2 agents + 1 judge** (validate the mechanics: independent
   histories, turn-taking, termination) before scaling to 5+2. This is the fastest
   way to catch prompt/orchestration bugs cheaply.
2. **Phase 2 — Scale to 5 agents**, add fact-checker role, add repetition detector.
3. **Phase 3 — Add second judge**, build the agreement/disagreement + tie-break logic.
4. **Phase 4 — Logging & eval**: run a batch of debates on known-answer questions
   (for ensemble mode) or held-out claims (for adversarial mode), measure whether the
   judged outcome beats a single-agent baseline. This is the step that tells you
   whether the extra cost of 5 agents + 2 judges is actually earning its keep.
5. **Phase 5 — UI + persistence**, only after Phase 4 shows the core loop adds value.

---

## 9. Key pitfalls to design against

- **Sycophancy/premature convergence**: mitigated by stance-locking + independent
  histories (Section 3) — the single biggest failure mode in naive multi-agent setups.
- **Judge self-preference bias**: mitigated by keeping judges model-distinct from
  debaters where possible (Section 4).
- **Context bloat**: transcript grows every round × 5 agents — summarize rounds older
  than the last 2 for agents that don't need verbatim history; keep full transcript
  only for judges at the end.
- **Cost blowup**: 5 agents × 3 rounds × 2 judges + possible tie-break ≈ 20-25 calls
  per debate minimum. Cap rounds hard, and consider a cheaper/faster model for the
  fact-checker role since its task (flag unsupported claims) is simpler than open
  debate.
- **First-mover advantage**: randomize speaking order each round rather than fixed
  round-robin position.

---

## 10. Evaluation — how to know if it's working

Don't just eyeball transcripts. For ensemble mode, run on a benchmark with known
correct answers (e.g. a set of factual/reasoning questions) and measure:
- Accuracy of the judged final answer vs. a single-agent baseline answer
- Judge A/Judge B agreement rate (track over time — low agreement flags rubric issues)
- Average rounds-to-termination (if every debate hits max rounds, agents aren't
  actually resolving disagreement — investigate prompts)

For adversarial mode without ground truth, use human spot-checks on a sample of
debates against the judges' verdicts to sanity-check the rubric is capturing what
you actually care about.
