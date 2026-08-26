"""$/million-token rates used to estimate real cost from real token usage.

Anthropic rates are first-party (verified against Anthropic's own published
pricing at the time this was written). OpenAI/Gemini/NVIDIA NIM rates were
pulled from third-party pricing aggregators, not the providers' own pricing
pages directly — LLM API pricing changes often (two models below were
retired or repriced within months of being added here), so treat these as a
reasonable starting point, not a guarantee, and re-verify before relying on
the dollar figures for anything beyond rough budgeting.

A (provider, model) pair not in this table returns None from
estimate_cost_usd rather than silently defaulting to some other model's
rate — an unpriced call should show up as "cost unknown" in the UI, never
as a fabricated number.
"""

# (provider, model) -> (input $ / 1M tokens, output $ / 1M tokens)
PRICING: dict[tuple[str, str], tuple[float, float]] = {
    # Anthropic — anthropic.com pricing.
    ("anthropic", "claude-fable-5"): (10.00, 50.00),
    ("anthropic", "claude-opus-5"): (5.00, 25.00),
    ("anthropic", "claude-sonnet-5"): (2.00, 10.00),
    ("anthropic", "claude-haiku-4-5"): (1.00, 5.00),
    # OpenAI — third-party aggregated, verify against platform.openai.com/pricing.
    ("openai", "gpt-4o"): (2.50, 10.00),
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("openai", "gpt-4.1"): (2.00, 8.00),
    ("openai", "o3-mini"): (1.10, 4.40),
    # Gemini — third-party aggregated, verify against ai.google.dev/pricing.
    # Base (<=200K context) tier only; gemini-2.5-pro is billed higher above 200K.
    ("gemini", "gemini-2.5-pro"): (1.25, 10.00),
    ("gemini", "gemini-2.5-flash"): (0.15, 1.25),
    # gemini-2.0-flash has no current entry — Google retired it in 2026;
    # deliberately left unpriced rather than showing a stale rate.
    # NVIDIA NIM — nvidia/llama-3.1-nemotron-super-49b-v1 and
    # nvidia/nemotron-nano-9b-v2 (the models this table used to price) were
    # retired from NVIDIA's catalog and replaced in the curated list with
    # nvidia/nemotron-3-super-120b-a12b and nvidia/nemotron-3-nano-30b-a3b —
    # confirmed live via /v1/models, but their per-model rates haven't been
    # verified against build.nvidia.com/pricing yet, so deliberately left
    # unpriced rather than carrying forward the old, now-wrong rates.
}


def estimate_cost_usd(provider: str, model: str, input_tokens: int, output_tokens: int) -> float | None:
    rates = PRICING.get((provider, model))
    if rates is None:
        return None
    input_rate, output_rate = rates
    return (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
