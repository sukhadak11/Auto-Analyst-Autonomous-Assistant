import pandas as pd
from pathlib import Path
import sys

from graph_state import AgentState
from explanation_schema import format_explanations

sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from visualization_logic import select_and_generate_visualizations


def visualization_agent_node(state: AgentState) -> AgentState:
    clean_path = state.get("clean_path", "data/clean_data.csv")
    target_col = state.get("target_col")
    job_id = state.get("job_id", "manual_test")

    df = pd.read_csv(clean_path)
    charts, explanations = select_and_generate_visualizations(
        df=df,
        target_col=target_col,
        question=state["question"],
        feature_importance=state.get("feature_importance", []),
        job_id=job_id,
    )

    state["generated_charts"] = charts  # add this field to graph_state.py
    state["explanations"] = state.get("explanations", []) + explanations
    state["data_findings"] = state.get("data_findings", "") + "\n" + format_explanations(explanations)
    state["messages"] = state.get("messages", []) + [f"Visualization Agent: generated {len(charts)} chart(s)."]
    return state


if __name__ == "__main__":
    test_state = {
        "question": "Show me a chart comparing churn rates and the top drivers.",
        "target_col": "churn",
        "clean_path": "data\\clean_data_7d38e694-b277-46.csv",
        "feature_importance": [("customer_service_calls", 0.45), ("total_charge", 0.32), ("international_plan", 0.28)],
        "job_id": "viz_test",
        "explanations": [], "messages": [],
    }
    result = visualization_agent_node(test_state)
    print(result["data_findings"])
    print("Charts generated:", result["generated_charts"])