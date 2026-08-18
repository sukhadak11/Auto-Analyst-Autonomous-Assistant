import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from feature_selection_logic import analyze_and_select_features
from explanation_schema import format_explanations
from graph_state import AgentState


def feature_selection_agent_node(state: AgentState) -> AgentState:
    clean_path = state.get("clean_path", "data/clean_data.csv")
    target_col = state.get("target_col")

    df = pd.read_csv(clean_path)
    transformed_df, explanations, final_cols = analyze_and_select_features(df, target_col)

    transformed_df.to_csv(clean_path, index=False)

    state["explanations"] = state.get("explanations", []) + explanations
    state["data_findings"] = state.get("data_findings", "") + "\n" + format_explanations(explanations)
    state["messages"] = state.get("messages", []) + ["Feature Selection Agent: analysis complete."]
    return state

'''
if __name__ == "__main__":
    test_state = {
        "target_col": "Loan_Status",
        "clean_path": "data/clean_data_loan_test.csv",   # <-- must exactly match the path Cleaning just printed
        "explanations": [], "messages": []
    }
    result = feature_selection_agent_node(test_state)
    print(result["data_findings"])
    '''