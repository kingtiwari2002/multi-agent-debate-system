import { formatCost, formatLatency } from "../format";

function VerdictCard({ verdict, label }) {
  const isRubric = verdict.judge_id === "judge_a_rubric";
  const scores = verdict.scores || {};
  const latency = formatLatency(verdict.latency_seconds);

  return (
    <div className="verdict-card">
      <h4>{label}</h4>
      <p className="verdict-card__winner">
        Winner: <strong>{verdict.winner || "—"}</strong>
        {latency && (
          <span className="verdict-card__stats">
            {" · "}
            {latency} · {formatCost(verdict.cost_usd)}
          </span>
        )}
      </p>
      {isRubric ? (
        <table className="rubric-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Factual</th>
              <th>Logic</th>
              <th>Responsive</th>
              <th>Clarity</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(scores).map(([agentId, s]) => (
              <tr key={agentId}>
                <td>{agentId}</td>
                <td>{s.factual_accuracy ?? "—"}</td>
                <td>{s.logical_validity ?? "—"}</td>
                <td>{s.responsiveness ?? "—"}</td>
                <td>{s.clarity ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="audit-points">
          <p>
            <strong>Strongest unrefuted:</strong> {scores.strongest_unrefuted_point?.agent_id || "—"}
            {scores.strongest_unrefuted_point?.point ? ` — ${scores.strongest_unrefuted_point.point}` : ""}
          </p>
          <p>
            <strong>Weakest unrefuted:</strong> {scores.weakest_unrefuted_point?.agent_id || "—"}
            {scores.weakest_unrefuted_point?.point ? ` — ${scores.weakest_unrefuted_point.point}` : ""}
          </p>
        </div>
      )}
      <p className="verdict-card__reasoning">{verdict.reasoning}</p>
    </div>
  );
}

export default function JudgePanel({ judgeVerdicts, judgesAgreed, tieBreakTriggered, finalWinner, disagreementRate, judgeAConfig, judgeBConfig }) {
  if (!judgeVerdicts || judgeVerdicts.length === 0) return null;

  const initial = judgeVerdicts.slice(0, 2);
  const retry = judgeVerdicts.slice(2, 4);
  const labelFor = (v, suffix) => {
    const isA = v.judge_id === "judge_a_rubric";
    const config = isA ? judgeAConfig : judgeBConfig;
    const base = isA ? "Judge A — Rubric Scorer" : "Judge B — Adversarial Auditor";
    return `${base}${config?.model ? ` (${config.model})` : ""}${suffix}`;
  };

  return (
    <div className="judge-panel">
      <div className="judge-panel__header">
        <h3>Judgment</h3>
        <span className={`badge ${judgesAgreed ? "badge--agree" : "badge--disagree"}`}>
          {judgesAgreed ? "Judges agreed" : "Judges disagreed"}
        </span>
        {typeof disagreementRate === "number" && (
          <span className="judge-panel__rate">All-time disagreement rate: {(disagreementRate * 100).toFixed(0)}%</span>
        )}
      </div>

      <div className="judge-panel__cards">
        {initial.map((v, i) => (
          <VerdictCard key={i} verdict={v} label={labelFor(v, tieBreakTriggered ? " (initial)" : "")} />
        ))}
      </div>

      {tieBreakTriggered && (
        <div className="judge-panel__tiebreak">
          <h4>Tie-break round triggered — judges' reasoning was fed back to debaters for one final rebuttal</h4>
          {retry.length > 0 && (
            <div className="judge-panel__cards">
              {retry.map((v, i) => (
                <VerdictCard key={i} verdict={v} label={labelFor(v, " (after tie-break)")} />
              ))}
            </div>
          )}
        </div>
      )}

      <p className="judge-panel__final">
        Final winner: <strong>{finalWinner || "Unresolved — flagged for human review"}</strong>
      </p>
    </div>
  );
}
