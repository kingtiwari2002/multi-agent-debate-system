import { useState } from "react";

const PROVIDERS = [
  { value: "anthropic", label: "Anthropic" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Gemini" },
  { value: "nvidia_nim", label: "NVIDIA NIM" },
  { value: "agentrouter", label: "AgentRouter (OpenAI)" },
  { value: "agentrouter_anthropic", label: "AgentRouter (Anthropic)" },
];

const MODELS_BY_PROVIDER = {
  anthropic: ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5", "claude-fable-5"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o3-mini"],
  gemini: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
  nvidia_nim: [
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nemotron-3-nano-30b-a3b",
  ],
  // AgentRouter routes by model name to the underlying provider, so the useful
  // model lists are the same ones as the provider it's fronting.
  agentrouter: ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o3-mini"],
  agentrouter_anthropic: ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5", "claude-fable-5"],
};

function modelOptionsFor(provider, currentModel) {
  const options = MODELS_BY_PROVIDER[provider] || [];
  return options.includes(currentModel) ? options : [currentModel, ...options];
}

function ProviderSelect({ value, disabled, onChange }) {
  return (
    <select value={value} disabled={disabled} onChange={onChange}>
      {PROVIDERS.map((p) => (
        <option key={p.value} value={p.value}>
          {p.label}
        </option>
      ))}
    </select>
  );
}

function AgentRow({ agent, onChange, disabled }) {
  return (
    <div className="config-row">
      <span className="config-row__id">
        {agent.agent_id}
        {agent.role === "fact_checker" && <span className="badge config-row__role">fact-checker</span>}
      </span>
      <ProviderSelect
        value={agent.provider}
        disabled={disabled}
        onChange={(e) => {
          const provider = e.target.value;
          const model = (MODELS_BY_PROVIDER[provider] || [])[0] || agent.model;
          onChange({ ...agent, provider, model });
        }}
      />
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
      <ProviderSelect
        value={judge.provider}
        disabled={disabled}
        onChange={(e) => {
          const provider = e.target.value;
          const model = (MODELS_BY_PROVIDER[provider] || [])[0] || judge.model;
          onChange({ ...judge, provider, model });
        }}
      />
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
