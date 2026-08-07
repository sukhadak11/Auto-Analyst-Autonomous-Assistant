# src/agent/graph.py
import sqlite3
import uuid
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graph_state import AgentState
from planner import plan_node
from data_agent import data_agent_node
from research_agent import research_agent_node
from report_agent import report_agent_node
from critic_agent import critic_node
from human_checkpoint import human_checkpoint_node


MAX_REVISIONS = 1


def route_after_critic(state: AgentState) -> str:
    if state.get("approved", False):
        return "end"
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return "end"
    return "revise"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", plan_node)
    graph.add_node("data_agent", data_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("report_agent", report_agent_node)
    graph.add_node("critic", critic_node)
    graph.add_node("human_checkpoint", human_checkpoint_node)   # <-- new

    graph.set_entry_point("planner")
    graph.add_edge("planner", "data_agent")
    graph.add_edge("data_agent", "research_agent")
    graph.add_edge("research_agent", "report_agent")
    graph.add_edge("report_agent", "critic")

    def route_after_critic(state: AgentState) -> str:
        if state.get("approved", False):
            return "human_checkpoint"          # clean approval -> still goes to human
        if state.get("revision_count", 0) >= MAX_REVISIONS:
            return "human_checkpoint"          # exhausted retries -> human decides
        return "revise"

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"revise": "report_agent", "human_checkpoint": "human_checkpoint"},
    )

    graph.add_edge("human_checkpoint", END)    # <-- terminal node now

    conn = sqlite3.connect("data/memory.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return graph.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    app = build_graph()

    thread_id = f"test_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"DEBUG: using thread_id = {thread_id}")

    initial_state = {
    "question": "Why might churn be spiking?",
    "plan": [], "data_findings": "", "research_findings": "",
    "report": "", "critique": "", "approved": False, "revision_count": 0,
    "human_decision": "", "human_notes": "",
    "messages": [],
}

    print("DEBUG: initial_state keys =", list(initial_state.keys()))
    print("DEBUG: question value =", initial_state.get("question"))

    final_state = app.invoke(initial_state, config=config)

    print("\n=== FINAL REPORT ===\n")
    print(final_state["report"])
    print("\n=== CRITIC VERDICT ===\n")
    print(final_state["critique"])
    print("\nApproved:", final_state["approved"])
    print("Revisions used:", final_state["revision_count"])
    print("\nFinal human decision:", final_state.get("human_decision"))