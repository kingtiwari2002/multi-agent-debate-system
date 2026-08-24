import { useState } from "react";
import HistoryTable from "../components/HistoryTable";
import ReplayView from "../components/ReplayView";

export default function HistoryView() {
  const [selectedRunId, setSelectedRunId] = useState(null);

  if (selectedRunId) {
    return <ReplayView runId={selectedRunId} onBack={() => setSelectedRunId(null)} />;
  }
  return <HistoryTable onSelect={setSelectedRunId} />;
}
