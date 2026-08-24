export default function FactCheckPanel({ flags }) {
  if (flags.length === 0) return null;
  return (
    <div className="fact-check-panel">
      <h3>Fact-check flags</h3>
      <ul>
        {flags.map((f, i) => (
          <li key={i}>
            <strong>{f.agent_id}</strong> (round {f.round}): "{f.claim}" — {f.reason}
          </li>
        ))}
      </ul>
    </div>
  );
}
