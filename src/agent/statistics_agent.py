import pandas as pd
from pathlib import Path
from graph_state import AgentState
from explanation_schema import format_explanations
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from src.pipeline.statistics_logic import compute_statistical_insights
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