import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graph_state import AgentState
from planner import plan_node
from profiling_agent import profiling_agent_node
from cleaning_agent import cleaning_agent_node
from feature_selection_agent import feature_selection_agent_node
from model_training_agent import model_training_agent_node
from statistics_agent import statistics_agent_node
from visualization_agent import visualization_agent_node
from research_agent import research_agent_node
from report_agent import report_agent_node
from critic_agent import critic_node

MAX_REVISIONS = 3


def route_after_profiling(state: AgentState) -> str:
    """Now that dataset_type is known, add time_series to required_agents
    if it's genuinely warranted (safety net — Planner already tries to do
    this, but dataset_type wasn't known yet when Planner ran)."""
    required = state.get("required_agents", [])
    if state.get("dataset_type") == "time_series" and "time_series" not in required:
        required.append("time_series")
    state["required_agents"] = required
    return "cleaning_agent"


def route_after_model_training(state: AgentState) -> str:
    required = state.get("required_agents", [])
    if "statistics" in required:
        return "statistics_agent"
    if "visualization" in required:
        return "visualization_agent"
    return "research_agent"


def route_after_statistics(state: AgentState) -> str:
    required = state.get("required_agents", [])
    if "visualization" in required:
        return "visualization_agent"
    return "research_agent"


def route_after_critic(state: AgentState) -> str:
    if state.get("approved", False):
        return "end"
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return "end"
    return "revise"


def build_graph_for_api():
    graph = StateGraph(AgentState)

    graph.add_node("planner", plan_node)
    graph.add_node("profiling_agent", profiling_agent_node)
    graph.add_node("cleaning_agent", cleaning_agent_node)
    graph.add_node("feature_selection_agent", feature_selection_agent_node)
    graph.add_node("model_training_agent", model_training_agent_node)
    graph.add_node("statistics_agent", statistics_agent_node)
    graph.add_node("visualization_agent", visualization_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("report_agent", report_agent_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "profiling_agent")

    # profiling routes to cleaning via a function, since it also patches required_agents
    graph.add_conditional_edges(
        "profiling_agent", route_after_profiling,
        {"cleaning_agent": "cleaning_agent"},
    )

    graph.add_edge("cleaning_agent", "feature_selection_agent")
    graph.add_edge("feature_selection_agent", "model_training_agent")

    # after model training, conditionally detour to statistics and/or visualization
    graph.add_conditional_edges(
        "model_training_agent", route_after_model_training,
        {
            "statistics_agent": "statistics_agent",
            "visualization_agent": "visualization_agent",
            "research_agent": "research_agent",
        },
    )

    graph.add_conditional_edges(
        "statistics_agent", route_after_statistics,
        {
            "visualization_agent": "visualization_agent",
            "research_agent": "research_agent",
        },
    )

    # visualization always proceeds to research next, regardless of how it was reached
    graph.add_edge("visualization_agent", "research_agent")

    graph.add_edge("research_agent", "report_agent")
    graph.add_edge("report_agent", "critic")

    graph.add_conditional_edges(
        "critic", route_after_critic,
        {"revise": "report_agent", "end": END},
    )

    conn = sqlite3.connect("data/memory.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return graph.compile(checkpointer=checkpointer)