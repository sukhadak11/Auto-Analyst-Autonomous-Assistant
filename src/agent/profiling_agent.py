# src/agent/profiling_agent.py
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from src.pipeline.profiling_logic import profile_dataset
from src.agent.explanation_schema import format_explanations
from src.agent.graph_state import AgentState



def profiling_agent_node(state: AgentState) -> AgentState:
    raw_path = state["raw_path"]
    user_target = state.get("user_specified_target")

    df = pd.read_csv(raw_path)
    profile = profile_dataset(df, user_specified_target=user_target)

    state["target_col"] = profile["target_col"]
    state["dataset_type"] = profile["dataset_type"]
    state["id_cols"] = profile["id_cols"]
    state["explanations"] = state.get("explanations", []) + profile["explanations"]
    state["data_findings"] = state.get("data_findings", "") + \
        f"\nDataset profile: {df.shape[0]} rows, {df.shape[1]} columns. " \
        f"Target: '{profile['target_col']}'. Type: {profile['dataset_type']}.\n" + \
        format_explanations(profile["explanations"])
    state["messages"] = state.get("messages", []) + ["Profiling Agent: dataset analyzed dynamically."]
    return state

'''
if __name__ == "__main__":
    # test with NO target/dataset assumptions hardcoded — only the file path
    test_state = {"raw_path": "data/telecommunications_churn.csv", "explanations": [], "messages": []}
    result = profiling_agent_node(test_state)
    print(result["data_findings"])
'''