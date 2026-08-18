# src/agent/cleaning_agent.py
import pandas as pd
from pathlib import Path
from graph_state import AgentState
from explanation_schema import format_explanations
import importlib.util

# Dynamically load pipeline/cleaning_logic.py to avoid relying on sys.path
module_path = Path(__file__).resolve().parents[1] / "pipeline" / "cleaning_logic.py"
spec = importlib.util.spec_from_file_location("cleaning_logic", str(module_path))
cleaning_logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleaning_logic)
analyze_and_clean = cleaning_logic.analyze_and_clean


def cleaning_agent_node(state: AgentState) -> AgentState:
    raw_path = state.get("raw_path")
    target_col = state.get("target_col")
    job_id = state.get("job_id")

    df = pd.read_csv(raw_path)
    cleaned_df, explanations = analyze_and_clean(df, target_col)

    clean_path = f"data/clean_data_{job_id}.csv"
    cleaned_df.to_csv(clean_path, index=False)

    state["clean_path"] = clean_path 
    state["explanations"] = state.get("explanations", []) + explanations
    state["data_findings"] = state.get("data_findings", "") + \
        f"\nCleaning complete: {cleaned_df.shape[0]} rows, {cleaned_df.shape[1]} columns.\n" + \
        format_explanations(explanations)
    state["messages"] = state.get("messages", []) + [f"Cleaning Agent: {len(explanations)} decisions logged."]
    return state

# quick test at the bottom of cleaning_agent.py
if __name__ == "__main__":
    test_state = {
        "raw_path": "data\\Excel\\loan prediction.csv",
        "target_col": "Loan_Status",
        "job_id": "loan_test",   # <-- add this
        "explanations": [], "messages": []
    }
    result = cleaning_agent_node(test_state)
    print(result["data_findings"])
    print("Clean path:", result["clean_path"])   # <-- add this so you can SEE exactly what path was used