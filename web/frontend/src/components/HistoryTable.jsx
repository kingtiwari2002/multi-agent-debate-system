import { useEffect, useState } from "react";
import { fetchHistory } from "../api";

export default function HistoryTable({ onSelect }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchHistory()
      .then(setRuns)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="view-status">Loading history…</p>;
  if (error) return <p className="view-status view-status--error">{error}</p>;
  if (runs.length === 0) return <p className="view-status">No debates run yet — start one from the "New debate" tab.</p>;

  return (
    <table className="history-table">
      <thead>
        <tr>
          <th>Topic</th>
          <th>Mode</th>
          <th>Winner</th>
          <th>Agreed</th>
          <th>LLM calls</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((r) => (
          <tr key={r.run_id} className="history-table__row" onClick={() => onSelect(r.run_id)}>
            <td>{r.topic}</td>
            <td>{r.mode}</td>
            <td>{r.final_winner || "—"}</td>
            <td>{r.judges_agreed ? "yes" : "no"}</td>
            <td>{r.total_llm_calls ?? "—"}</td>
            <td>{new Date(r.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
