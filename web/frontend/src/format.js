export function formatCost(usd) {
  if (usd === null || usd === undefined) return "cost unknown";
  return `$${usd.toFixed(4)}`;
}

export function formatLatency(seconds) {
  if (!seconds) return null;
  return `${seconds.toFixed(1)}s`;
}
