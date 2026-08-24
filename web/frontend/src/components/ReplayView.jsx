import { useEffect, useState } from "react";
import { fetchDebate } from "../api";
import AgentColumn from "./AgentColumn";
import FactCheckPanel from "./FactCheckPanel";
import JudgePanel from "./JudgePanel";

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
