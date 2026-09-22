from src.agent.adalflow.report_generator import AdalFlowReportGenerator


# Create once and reuse
adalflow_report_generator = AdalFlowReportGenerator()


def adalflow_report_agent_node(state):
    """
    Generate the AutoAnalyst report using AdalFlow
    while preserving the existing AgentState.
    """

    response = adalflow_report_generator.generate_from_state(state)

    if response.data is None:
        raise RuntimeError(
            "AdalFlow failed to generate a structured report."
        )

    report = response.data

    # Convert structured AdalFlow output
    # into the format expected by AutoAnalyst.
    full_report = (
        f"## Answer\n"
        f"{report.answer}\n\n"
        f"## Recommendation\n"
        f"{report.recommendation}\n\n"
        f"## Key Findings\n"
    )

    for finding in report.key_findings:
        full_report += f"- {finding}\n"

    # Store report in existing AgentState
    state["report"] = full_report

    # Store structured information as well.
    # This can be useful for the Critic Agent later.
    state["adalflow_report"] = {
        "answer": report.answer,
        "recommendation": report.recommendation,
        "key_findings": report.key_findings,
    }

    # Preserve existing messages
    state["messages"] = state.get("messages", []) + [
        "AdalFlow Report Agent generated a structured report."
    ]

    # Preserve revision tracking
    state["revision_count"] = state.get("revision_count", 0) + 1

    return state