import { formatCost, formatLatency } from "../format";

export default function AgentColumn({ agentId, statements, isDropped }) {
  return (
    <div className={`agent-column${isDropped ? " agent-column--dropped" : ""}`}>
      <div className="agent-column__header">
        <span className="agent-column__id">{agentId}</span>
        {isDropped && <span className="badge badge--dropped">dropped</span>}
      </div>
      <div className="agent-column__body">
        {statements.length === 0 && <p className="agent-column__empty">Waiting…</p>}
        {statements.map((s, i) => {
          const latency = formatLatency(s.latency_seconds);
          return (
            <div key={i} className={`statement statement--${s.phase}`}>
              <div className="statement__meta">
                <span className="badge">{s.phase === "tie_break" ? "tie-break" : s.phase}</span>
                <span className="statement__round">Round {s.round}</span>
                {latency && (
                  <span className="statement__stats">
                    {latency} · {formatCost(s.cost_usd)}
                  </span>
                )}
              </div>
              <p>{s.content}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
