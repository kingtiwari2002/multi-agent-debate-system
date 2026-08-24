import { useState } from "react";

export default function DebateForm({ onStart, disabled }) {
  const [topic, setTopic] = useState("");
  const [mode, setMode] = useState("adversarial");
  const [rounds, setRounds] = useState(3);

  function handleSubmit(e) {
    e.preventDefault();
    if (!topic.trim()) return;
    onStart(topic.trim(), mode, Number(rounds));
  }

  return (
    <form className="debate-form" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder={mode === "adversarial" ? "e.g. Remote work improves productivity" : "e.g. What is the best sorting algorithm for nearly-sorted data?"}
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        disabled={disabled}
        required
      />
      <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={disabled}>
        <option value="adversarial">Adversarial (2 pro / 2 con / fact-checker)</option>
        <option value="ensemble">Ensemble (5 independent solvers)</option>
      </select>
      <input
        type="number"
        min={1}
        max={10}
        value={rounds}
        onChange={(e) => setRounds(e.target.value)}
        disabled={disabled}
        title="Max rounds"
      />
      <button type="submit" disabled={disabled}>
        {disabled ? "Debate running…" : "Start debate"}
      </button>
    </form>
  );
}
