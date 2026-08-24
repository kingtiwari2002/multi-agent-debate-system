from .models import AgentConfig


def build_adversarial_agents() -> list[AgentConfig]:
    # 2 pro / 2 con / 1 fact-checker. 4 on Claude with distinct personas, 1 on a
    # different model family (con_2) to avoid correlated blind spots; fact-checker
    # runs on a cheaper model since its task is simpler than open debate.
    return [
        AgentConfig(
            agent_id="agent_pro_1",
            persona="Sharp, evidence-driven advocate.",
            position="Argue FOR the resolution.",
            provider="anthropic",
            model="claude-sonnet-5",
            temperature=0.7,
        ),
        AgentConfig(
            agent_id="agent_pro_2",
            persona="Pragmatic, real-world-examples advocate.",
            position="Argue FOR the resolution.",
            provider="anthropic",
            model="claude-sonnet-5",
            temperature=0.9,
        ),
        AgentConfig(
            agent_id="agent_con_1",
            persona="Skeptical, detail-oriented critic.",
            position="Argue AGAINST the resolution.",
            provider="anthropic",
            model="claude-sonnet-5",
            temperature=0.7,
        ),
        AgentConfig(
            agent_id="agent_con_2",
            persona="Contrarian, first-principles critic.",
            position="Argue AGAINST the resolution.",
            provider="openai",
            model="gpt-4o",
            temperature=0.8,
        ),
        AgentConfig(
            agent_id="fact_checker",
            persona="Neutral, terse claim auditor.",
            position="Do not argue a side — flag unsupported claims only.",
            provider="anthropic",
            model="claude-haiku-4-5",
            temperature=0.0,
            role="fact_checker",
        ),
    ]


def build_ensemble_agents() -> list[AgentConfig]:
    # 5 independent solvers, no fixed stance — roles emerge in rebuttal.
    # 4 on Claude with varied personas/temperature, 1 on a different family.
    personas = [
        ("solver_1", "anthropic", "claude-sonnet-5", 0.5, "Methodical, step-by-step reasoner."),
        ("solver_2", "anthropic", "claude-sonnet-5", 0.9, "Creative, lateral-thinking problem solver."),
        ("solver_3", "anthropic", "claude-sonnet-5", 0.3, "Conservative, evidence-first reasoner."),
        ("solver_4", "anthropic", "claude-sonnet-5", 0.7, "Devil's-advocate stress-tester."),
        ("solver_5", "openai", "gpt-4o", 0.6, "Independent second-opinion solver."),
    ]
    return [
        AgentConfig(
            agent_id=agent_id,
            persona=persona,
            position="Independently solve the problem, then be ready to defend or revise your answer.",
            provider=provider,
            model=model,
            temperature=temperature,
        )
        for agent_id, provider, model, temperature, persona in personas
    ]


def build_agents(mode: str) -> list[AgentConfig]:
    return build_adversarial_agents() if mode == "adversarial" else build_ensemble_agents()
