import pandas as pd
import joblib
from pathlib import Path
from graph_state import AgentState
from explanation_schema import format_explanations
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from model_training_logic import train_and_compare_models


def model_training_agent_node(state: AgentState) -> AgentState:
    clean_path = state.get("clean_path", "data/clean_data.csv")
    target_col = state.get("target_col")
    needs_interpretability = state.get("needs_interpretability", True)
    job_id = state.get("job_id", "manual_test")

    df = pd.read_csv(clean_path)
    model, model_name, X_test, y_test, test_score, explanations = train_and_compare_models(
        df, target_col, needs_interpretability
    )

    model_path = f"data/model_{job_id}.joblib"
    joblib.dump(model, model_path)

    state["model_path"] = model_path
    state["model_name"] = model_name
    state["explanations"] = state.get("explanations", []) + explanations
    state["data_findings"] = state.get("data_findings", "") + "\n" + format_explanations(explanations)
    state["messages"] = state.get("messages", []) + [f"Model Training Agent: selected {model_name}."]
    return state

'''
if __name__ == "__main__":
    test_state = {
        "target_col": "churn",
        "clean_path": "data/clean_data_telecom_test.csv",
        "needs_interpretability": True,
        "job_id": "telecom_test",
        "explanations": [], "messages": []
    }
    result = model_training_agent_node(test_state)
    print(result["data_findings"])
    print("Model saved to:", result["model_path"])
    '''