import { useState } from "react";

const MODELS_BY_PROVIDER = {
  anthropic: ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5", "claude-fable-5"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o3-mini"],
};

function modelOptionsFor(provider, currentModel) {
  const options = MODELS_BY_PROVIDER[provider] || [];
  return options.includes(currentModel) ? options : [currentModel, ...options];
}

function AgentRow({ agent, onChange, disabled }) {
  return (
    <div className="config-row">
      <span className="config-row__id">
        {agent.agent_id}
        {agent.role === "fact_checker" && <span className="badge config-row__role">fact-checker</span>}
      </span>
      <select
        value={agent.provider}
        disabled={disabled}
        onChange={(e) => {
          const provider = e.target.value;
          const model = (MODELS_BY_PROVIDER[provider] || [])[0] || agent.model;
          onChange({ ...agent, provider, model });
        }}
      >
        <option value="anthropic">Anthropic</option>
        <option value="openai">OpenAI</option>
      </select>
      <select
        value={agent.model}
        disabled={disabled}
        onChange={(e) => onChange({ ...agent, model: e.target.value })}
      >
        {modelOptionsFor(agent.provider, agent.model).map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
      <input
        type="text"
        className="config-row__persona"
        value={agent.persona}
        disabled={disabled}
        onChange={(e) => onChange({ ...agent, persona: e.target.value })}
        title="Persona"
      />
      <input
        type="number"
        min={0}
        max={2}
        step={0.1}
        value={agent.temperature}
        disabled={disabled}
        onChange={(e) => onChange({ ...agent, temperature: Number(e.target.value) })}
        title="Temperature"
      />
    </div>
  );
}

function JudgeRow({ label, judge, onChange, disabled }) {
  return (
    <div className="config-row config-row--judge">
      <span className="config-row__id">{label}</span>
      <select
        value={judge.provider}
        disabled={disabled}
        onChange={(e) => {
          const provider = e.target.value;
          const model = (MODELS_BY_PROVIDER[provider] || [])[0] || judge.model;
          onChange({ ...judge, provider, model });
        }}
      >
        <option value="anthropic">Anthropic</option>
        <option value="openai">OpenAI</option>
      </select>
      <select
        value={judge.model}
        disabled={disabled}
        onChange={(e) => onChange({ ...judge, model: e.target.value })}
      >
        {modelOptionsFor(judge.provider, judge.model).map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function ConfigPanel({ agents, judgeA, judgeB, onAgentsChange, onJudgeAChange, onJudgeBChange, onReset, disabled }) {
  const [expanded, setExpanded] = useState(false);

  if (!agents.length) return null;

  function updateAgent(index, updated) {
    const next = agents.slice();
    next[index] = updated;
    onAgentsChange(next);
  }

  return (
    <div className="config-panel">
      <button type="button" className="config-panel__toggle" onClick={() => setExpanded((v) => !v)}>
        {expanded ? "▾" : "▸"} Agent &amp; judge config
      </button>
      {expanded && (
        <div className="config-panel__body">
          {agents.map((agent, i) => (
            <AgentRow key={agent.agent_id} agent={agent} disabled={disabled} onChange={(updated) => updateAgent(i, updated)} />
          ))}
          <JudgeRow label="Judge A — Rubric Scorer" judge={judgeA} disabled={disabled} onChange={onJudgeAChange} />
          <JudgeRow label="Judge B — Adversarial Auditor" judge={judgeB} disabled={disabled} onChange={onJudgeBChange} />
          <button type="button" className="config-panel__reset" onClick={onReset} disabled={disabled}>
            Reset to default
          </button>
        </div>
      )}
    </div>
  );
}
