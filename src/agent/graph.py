import sqlite3
import uuid
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.agent.graph_state import AgentState
from src.agent.planner import plan_node
from src.agent.profiling_agent import profiling_agent_node
from src.agent.cleaning_agent import cleaning_agent_node
from src.agent.feature_selection_agent import feature_selection_agent_node
from src.agent.model_training_agent import model_training_agent_node
from src.agent.research_agent import research_agent_node
from src.agent.report_agent import report_agent_node
from src.agent.critic_agent import critic_node
from src.agent.human_checkpoint import human_checkpoint_node

MAX_REVISIONS = 3


# graph.py — add this alongside the existing build_graph()

def build_graph_for_api():
    """Same pipeline as build_graph(), but stops after the Critic instead
    of calling human_checkpoint_node's blocking input(). The API's
    /approve endpoint handles human approval instead."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", plan_node)
    graph.add_node("profiling_agent", profiling_agent_node)
    graph.add_node("cleaning_agent", cleaning_agent_node)
    graph.add_node("feature_selection_agent", feature_selection_agent_node)
    graph.add_node("model_training_agent", model_training_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("report_agent", report_agent_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "profiling_agent")
    graph.add_edge("profiling_agent", "cleaning_agent")
    graph.add_edge("cleaning_agent", "feature_selection_agent")
    graph.add_edge("feature_selection_agent", "model_training_agent")
    graph.add_edge("model_training_agent", "research_agent")
    graph.add_edge("research_agent", "report_agent")
    graph.add_edge("report_agent", "critic")

    def route_after_critic(state: AgentState) -> str:
        if state.get("approved", False):
            return "end"
        if state.get("revision_count", 0) >= MAX_REVISIONS:
            return "end"
        return "revise"

    graph.add_conditional_edges(
        "critic", route_after_critic,
        {"revise": "report_agent", "end": END},
    )

    conn = sqlite3.connect("data/memory.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    app = build_graph_for_api()

    job_id = f"run_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": job_id}}
    print(f"DEBUG: job_id = {job_id}")

    initial_state = {
        "question": "Analyze this dataset and summarize the key findings.",
        "plan": [], "data_findings": "", "research_findings": "", "report": "",
        "critique": "", "approved": False, "revision_count": 0,
        "human_decision": "", "human_notes": "",
        "explanations": [],
        "raw_path": "data/Excel/telecommunications_churn.csv",  # only manual input needed
        "clean_path": "",
        "target_col": "",          # left empty — Profiling Agent fills this in
        "dataset_type": "",
        "id_cols": [],
        "needs_interpretability": True,
        "model_path": "", "model_name": "",
        "job_id": job_id,
        "messages": [],
    }

    final_state = app.invoke(initial_state, config=config)

    print("\n=== ALL EXPLANATIONS LOGGED ===")
    for e in final_state["explanations"]:
        print(f"- {e['action']} (confidence: {e['confidence']})")

    print("\n=== FINAL REPORT ===")
    print(final_state.get("report", "No report generated."))