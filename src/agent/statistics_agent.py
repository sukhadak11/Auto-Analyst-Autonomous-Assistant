import pandas as pd
from pathlib import Path
from graph_state import AgentState
from explanation_schema import format_explanations
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from statistics_logic import compute_statistical_insights


def statistics_agent_node(state: AgentState) -> AgentState:
    clean_path = state.get("clean_path", "data/clean_data.csv")
    target_col = state.get("target_col")

    df = pd.read_csv(clean_path)
    insights, explanations = compute_statistical_insights(df, target_col, state["question"])

    state["statistical_insights"] = insights  # add this field to graph_state.py
    state["explanations"] = state.get("explanations", []) + explanations
    state["data_findings"] = state.get("data_findings", "") + "\n" + format_explanations(explanations)
    state["messages"] = state.get("messages", []) + [f"Statistics Agent: {len(insights)} insight(s) computed."]
    return state


if __name__ == "__main__":
    test_state = {
        "question": "What statistical relationships exist between usage and churn?",
        "target_col": "churn",
        "clean_path": "data\\clean_data_7d38e694-b277-46.csv",
        "explanations": [], "messages": [],
    }
    result = statistics_agent_node(test_state)
    print(result["data_findings"])