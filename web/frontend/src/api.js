// Same-origin: the backend now serves this built frontend directly on port
// 55786, so requests go back to wherever the page itself was loaded from.
export const API_BASE = window.location.origin;

export async function fetchPresets(mode) {
  const res = await fetch(`${API_BASE}/api/presets/${mode}`);
  if (!res.ok) throw new Error(`Failed to fetch presets (${res.status})`);
  return res.json();
}

export async function startDebate(topic, mode, rounds, agents, judgeA, judgeB) {
  const res = await fetch(`${API_BASE}/api/debates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, mode, rounds, agents, judge_a: judgeA, judge_b: judgeB }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to start debate (${res.status})`);
  }
  return res.json();
}

export function connectDebateSocket(runId, handlers) {
  const ws = new WebSocket(`${API_BASE.replace("http", "ws")}/ws/debates/${runId}`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handlers.onEvent?.(data);
  };
  ws.onerror = () => handlers.onSocketError?.();
  ws.onclose = () => handlers.onClose?.();
  return ws;
}

export async function fetchHistory() {
  const res = await fetch(`${API_BASE}/api/debates`);
  if (!res.ok) throw new Error(`Failed to fetch history (${res.status})`);
  return res.json();
}

export async function fetchDebate(runId) {
  const res = await fetch(`${API_BASE}/api/debates/${runId}`);
  if (!res.ok) throw new Error(`Failed to fetch debate (${res.status})`);
  return res.json();
}
