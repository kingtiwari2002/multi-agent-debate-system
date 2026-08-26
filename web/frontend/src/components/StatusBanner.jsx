import { formatCost } from "../format";

const STATUS_TEXT = {
  idle: "Enter a topic to start a debate.",
  connecting: "Connecting…",
  running: "Debate in progress…",
  done: "Debate complete.",
  error: "Something went wrong.",
};

export default function StatusBanner({ status, finalRun, errorMessage, tieBreakTriggered }) {
  return (
    <div className={`status-banner status-banner--${status}`}>
      {(status === "connecting" || status === "running") && <span className="spinner" aria-hidden="true" />}
      <span>{STATUS_TEXT[status]}</span>
      {tieBreakTriggered && status !== "done" && <span className="badge badge--tiebreak">tie-break round triggered</span>}
      {status === "error" && errorMessage && <span className="status-banner__error">{errorMessage}</span>}
      {status === "done" && finalRun && (
        <span className="status-banner__result">
          Winner: <strong>{finalRun.final_winner || "unresolved — flag for human review"}</strong>
          {" · "}Judges agreed: {finalRun.judges_agreed ? "yes" : "no"}
          {finalRun.tie_break_triggered ? " · tie-break was used" : ""}
          {typeof finalRun.total_llm_calls === "number" ? ` · ${finalRun.total_llm_calls} LLM calls` : ""}
          {typeof finalRun.total_latency_seconds === "number" ? ` · ${finalRun.total_latency_seconds.toFixed(1)}s total` : ""}
          {typeof finalRun.total_cost_usd === "number" ? ` · ~${formatCost(finalRun.total_cost_usd)}` : ""}
          {finalRun.unpriced_calls > 0 ? ` (${finalRun.unpriced_calls} call${finalRun.unpriced_calls === 1 ? "" : "s"} unpriced)` : ""}
        </span>
      )}
    </div>
  );
}
