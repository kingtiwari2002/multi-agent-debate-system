import { useState } from "react";
import "./App.css";
import LiveDebateView from "./views/LiveDebateView";
import HistoryView from "./views/HistoryView";

export default function App() {
  const [tab, setTab] = useState("debate"); // "debate" | "history"

  return (
    <div className="app">
      <header className="app__header">
        <h1>Multi-Agent Debate System</h1>
        <p className="app__subtitle">5 debating agents + 2 independent judges</p>
        <nav className="app__nav">
          <button className={tab === "debate" ? "app__nav-btn app__nav-btn--active" : "app__nav-btn"} onClick={() => setTab("debate")}>
            New debate
          </button>
          <button className={tab === "history" ? "app__nav-btn app__nav-btn--active" : "app__nav-btn"} onClick={() => setTab("history")}>
            History
          </button>
        </nav>
      </header>

      {tab === "debate" ? <LiveDebateView /> : <HistoryView />}
    </div>
  );
}
