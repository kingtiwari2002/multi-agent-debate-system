import { useCallback, useEffect, useRef, useState } from "react";
import DebateForm from "../components/DebateForm";
import AgentColumn from "../components/AgentColumn";
import FactCheckPanel from "../components/FactCheckPanel";
import StatusBanner from "../components/StatusBanner";
import JudgePanel from "../components/JudgePanel";
import ConfigPanel from "../components/ConfigPanel";
import { startDebate, connectDebateSocket, fetchPresets } from "../api";

export default function LiveDebateView() {
  const [status, setStatus] = useState("idle"); // idle | connecting | running | done | error
  const [mode, setMode] = useState("adversarial");
  const [agents, setAgents] = useState([]);
  const [judgeA, setJudgeA] = useState(null);
  const [judgeB, setJudgeB] = useState(null);
  const [agentOrder, setAgentOrder] = useState([]);
  const [statementsByAgent, setStatementsByAgent] = useState({});
  const [droppedAgents, setDroppedAgents] = useState(new Set());
  const [claimFlags, setClaimFlags] = useState([]);
  const [tieBreakTriggered, setTieBreakTriggered] = useState(false);
  const [finalRun, setFinalRun] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const wsRef = useRef(null);
  const doneReceivedRef = useRef(false);

  const loadPresets = useCallback((forMode) => {
    fetchPresets(forMode)
      .then(({ agents: defaultAgents, judge_a, judge_b }) => {
        setAgents(defaultAgents);
        setJudgeA(judge_a);
        setJudgeB(judge_b);
      })
      .catch(() => {
        // Config panel just stays empty/hidden if presets can't be loaded — the
        // debate can still start using the backend's own defaults.
      });
  }, []);

  useEffect(() => {
    loadPresets(mode);
  }, [mode, loadPresets]);

  function handleModeChange(nextMode) {
    setMode(nextMode);
  }

  const reset = useCallback(() => {
    setAgentOrder([]);
    setStatementsByAgent({});
    setDroppedAgents(new Set());
    setClaimFlags([]);
    setTieBreakTriggered(false);
    setFinalRun(null);
    setErrorMessage("");
    doneReceivedRef.current = false;
  }, []);

  const handleEvent = useCallback((event) => {
    switch (event.type) {
      case "statement": {
        const s = event.statement;
        setAgentOrder((prev) => (prev.includes(s.agent_id) ? prev : [...prev, s.agent_id]));
        setStatementsByAgent((prev) => ({
          ...prev,
          [s.agent_id]: [...(prev[s.agent_id] || []), s],
        }));
        if (s.phase === "dropped") {
          setDroppedAgents((prev) => new Set(prev).add(s.agent_id));
        }
        break;
      }
      case "claim_flags":
        setClaimFlags((prev) => [...prev, ...event.flags]);
        break;
      case "agent_dropped":
        setDroppedAgents((prev) => new Set(prev).add(event.agent_id));
        break;
      case "tie_break_triggered":
        setTieBreakTriggered(true);
        break;
      case "error":
        setErrorMessage(event.message);
        setStatus("error");
        break;
      case "done":
        doneReceivedRef.current = true;
        if (event.run) {
          setFinalRun(event.run);
          setStatus("done");
        } else {
          setStatus((prev) => (prev === "error" ? prev : "error"));
        }
        break;
      default:
        break;
    }
  }, []);

  async function handleStart(topic, rounds) {
    reset();
    setStatus("connecting");
    try {
      const { run_id } = await startDebate(topic, mode, rounds, agents, judgeA, judgeB);
      const ws = connectDebateSocket(run_id, {
        onEvent: (event) => {
          setStatus((prevStatus) => (prevStatus === "connecting" ? "running" : prevStatus));
          handleEvent(event);
        },
        onSocketError: () => setStatus("error"),
        onClose: () => {
          if (!doneReceivedRef.current) {
            setErrorMessage("Connection lost before the debate finished.");
            setStatus("error");
          }
        },
      });
      wsRef.current = ws;
    } catch (err) {
      setErrorMessage(err.message);
      setStatus("error");
    }
  }

  const isRunning = status === "connecting" || status === "running";

  return (
    <div>
      <DebateForm mode={mode} onModeChange={handleModeChange} onStart={handleStart} disabled={isRunning} />
      {judgeA && judgeB && (
        <ConfigPanel
          agents={agents}
          judgeA={judgeA}
          judgeB={judgeB}
          onAgentsChange={setAgents}
          onJudgeAChange={setJudgeA}
          onJudgeBChange={setJudgeB}
          onReset={() => loadPresets(mode)}
          disabled={isRunning}
        />
      )}
      <StatusBanner status={status} finalRun={finalRun} errorMessage={errorMessage} tieBreakTriggered={tieBreakTriggered} />
      <FactCheckPanel flags={claimFlags} />

      <div className="debate-board">
        {agentOrder.map((agentId) => (
          <AgentColumn
            key={agentId}
            agentId={agentId}
            statements={statementsByAgent[agentId] || []}
            isDropped={droppedAgents.has(agentId)}
          />
        ))}
      </div>

      {status === "done" && finalRun && (
        <JudgePanel
          judgeVerdicts={finalRun.judge_verdicts}
          judgesAgreed={finalRun.judges_agreed}
          tieBreakTriggered={finalRun.tie_break_triggered}
          finalWinner={finalRun.final_winner}
          disagreementRate={finalRun.disagreement_rate}
          judgeAConfig={finalRun.judge_a_config}
          judgeBConfig={finalRun.judge_b_config}
        />
      )}
    </div>
  );
}
