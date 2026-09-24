import pandas as pd

from pathlib import Path

from src.agent.graph_state import AgentState

from src.agent.explanation_schema import format_explanations

import importlib.util

# Database imports

from src.db.database import SessionLocal


# Dynamically load pipeline/cleaning_logic.py
# to avoid relying on sys.path
module_path = (
    Path(__file__).resolve().parents[1]
    / "pipeline"
    / "cleaning_logic.py"
)

spec = importlib.util.spec_from_file_location(
    "cleaning_logic",
    str(module_path),
)

cleaning_logic = importlib.util.module_from_spec(spec)

spec.loader.exec_module(cleaning_logic)

analyze_and_clean = cleaning_logic.analyze_and_clean


def cleaning_agent_node(state: AgentState) -> AgentState:

    raw_path = state.get("raw_path")
    target_col = state.get("target_col")
    job_id = state.get("job_id")

    # ------------------------------------------------------------
    # 1. READ DATASET
    # ------------------------------------------------------------

    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------
    # 2. CLEAN DATASET
    # ------------------------------------------------------------

    cleaned_df, explanations = analyze_and_clean(
        df,
        target_col,
    )

    # ------------------------------------------------------------
    # 3. SAVE CLEANED CSV TO FILESYSTEM
    # ------------------------------------------------------------

    project_root = Path(__file__).resolve().parents[2]

    csv_dir = (
        project_root
        / "data"
        / "output"
        / str(job_id)
        / "csv"
    )

    csv_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    clean_path = csv_dir / "cleaned_data.csv"

    cleaned_df.to_csv(
        clean_path,
        index=False,
    )

   
    # ------------------------------------------------------------
    # 5. UPDATE AGENT STATE
    # ------------------------------------------------------------

    state["clean_path"] = clean_path

    state["explanations"] = (
        state.get("explanations", [])
        + explanations
    )

    state["data_findings"] = (
        state.get("data_findings", "")
        + (
            f"\nCleaning complete: "
            f"{cleaned_df.shape[0]} rows, "
            f"{cleaned_df.shape[1]} columns.\n"
            + format_explanations(explanations)
        )
    )

    state["messages"] = (
        state.get("messages", [])
        + [
            f"Cleaning Agent: "
            f"{len(explanations)} decisions logged."
        ]
    )

    return state