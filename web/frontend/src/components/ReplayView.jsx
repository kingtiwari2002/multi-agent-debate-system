import { useEffect, useState } from "react";
import { fetchDebate } from "../api";
import AgentColumn from "./AgentColumn";
import FactCheckPanel from "./FactCheckPanel";
import JudgePanel from "./JudgePanel";
import { formatCost } from "../format";

export default function ReplayView({ runId, onBack }) {
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRun(null);
    setError("");
    fetchDebate(runId)
      .then(setRun)
      .catch((e) => setError(e.message));
  }, [runId]);

  return (
    <div>
      <button type="button" className="link-button" onClick={onBack}>
        &larr; Back to history
      </button>

      {error && <p className="view-status view-status--error">{error}</p>}
      {!run && !error && <p className="view-status">Loading run…</p>}

      {run && (
        <>
          <h2>{run.topic}</h2>
          <p className="replay-meta">
            {run.mode} · {new Date(run.created_at).toLocaleString()} · {run.max_rounds} rounds
            {typeof run.total_llm_calls === "number" ? ` · ${run.total_llm_calls} LLM calls` : ""}
            {typeof run.total_latency_seconds === "number" ? ` · ${run.total_latency_seconds.toFixed(1)}s total` : ""}
            {typeof run.total_cost_usd === "number" ? ` · ~${formatCost(run.total_cost_usd)}` : ""}
            {run.unpriced_calls > 0 ? ` (${run.unpriced_calls} call${run.unpriced_calls === 1 ? "" : "s"} unpriced)` : ""}
          </p>

          <FactCheckPanel flags={run.claim_flags || []} />

          <div className="debate-board">
            {groupByAgent(run.transcript).map(([agentId, statements]) => (
              <AgentColumn
                key={agentId}
                agentId={agentId}
                statements={statements}
                isDropped={(run.dropped_agents || []).includes(agentId)}
              />
            ))}
          </div>

          <JudgePanel
            judgeVerdicts={run.judge_verdicts}
            judgesAgreed={run.judges_agreed}
            tieBreakTriggered={run.tie_break_triggered}
            finalWinner={run.final_winner}
            disagreementRate={run.disagreement_rate}
            judgeAConfig={run.judge_a_config}
            judgeBConfig={run.judge_b_config}
          />
        </>
      )}
    </div>
  );
}

function groupByAgent(transcript) {
  const order = [];
  const byAgent = {};
  for (const s of transcript || []) {
    if (!byAgent[s.agent_id]) {
      byAgent[s.agent_id] = [];
      order.push(s.agent_id);
    }
    byAgent[s.agent_id].push(s);
  }
  return order.map((agentId) => [agentId, byAgent[agentId]]);
}
