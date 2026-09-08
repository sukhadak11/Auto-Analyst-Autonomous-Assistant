import pandas as pd
from pathlib import Path
import sys

from graph_state import AgentState
from explanation_schema import format_explanations, make_explanation

# Allow importing visualization_logic.py from src/pipeline
sys.path.append(
    str(Path(__file__).resolve().parents[1] / "pipeline")
)

from visualization_logic import (
    select_and_generate_visualizations
)


def visualization_agent_node(state: AgentState) -> AgentState:
    """
    Visualization Agent

    Responsibilities:
    1. Load the cleaned dataset.
    2. Understand the user's visualization request.
    3. Select suitable visualizations.
    4. Generate chart PNG files.
    5. Store chart metadata in state["generated_charts"].
    6. Store structured visualization explanations.
    """

    # --------------------------------------------------------
    # Get required values from state
    # --------------------------------------------------------

    clean_path = state.get(
        "clean_path",
        "data/clean_data.csv"
    )

    target_col = state.get("target_col")

    job_id = state.get(
        "job_id",
        "manual_test"
    )

    question = state.get(
        "question",
        ""
    )

    # --------------------------------------------------------
    # Validate cleaned dataset
    # --------------------------------------------------------

    clean_file = Path(clean_path)

    if not clean_file.exists():

        state["generated_charts"] = []

        error_message = (
            f"Visualization Agent could not find the "
            f"cleaned dataset: {clean_file}"
        )

        state["data_findings"] = (
            state.get("data_findings", "")
            + "\n"
            + error_message
        )

        state["messages"] = (
            state.get("messages", [])
            + [error_message]
        )

        return state

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    try:
        df = pd.read_csv(clean_file)

    except Exception as exc:

        error_message = (
            f"Visualization Agent failed to load "
            f"the cleaned dataset: {exc}"
        )

        state["generated_charts"] = []

        state["data_findings"] = (
            state.get("data_findings", "")
            + "\n"
            + error_message
        )

        state["messages"] = (
            state.get("messages", [])
            + [error_message]
        )

        return state

    # --------------------------------------------------------
    # Generate visualizations
    # --------------------------------------------------------

    try:

        charts, explanations = (
            select_and_generate_visualizations(
                df=df,
                target_col=target_col,
                question=question,
                feature_importance=state.get(
                    "feature_importance",
                    []
                ),
                job_id=job_id,
                output_dir="data/plots",
            )
        )

    except Exception as exc:

        error_message = (
            f"Visualization Agent failed while "
            f"generating visualizations: {exc}"
        )

        state["generated_charts"] = []

        state["data_findings"] = (
            state.get("data_findings", "")
            + "\n"
            + error_message
        )

        state["messages"] = (
            state.get("messages", [])
            + [error_message]
        )

        return state

    # --------------------------------------------------------
    # Validate chart metadata
    # --------------------------------------------------------

    if not isinstance(charts, list):
        charts = []

    valid_charts = []

    for chart in charts:

        if isinstance(chart, dict):

            valid_charts.append(chart)

        elif isinstance(chart, (tuple, list)) and len(chart) >= 2:

            # Backward compatibility with:
            # ("chart_type", "filename")

            valid_charts.append(
                {
                    "chart_type": chart[0],
                    "filename": chart[1],
                }
            )

    charts = valid_charts

    # --------------------------------------------------------
    # Store generated chart metadata
    # --------------------------------------------------------

    state["generated_charts"] = charts

    # --------------------------------------------------------
    # Normalize explanations
    # --------------------------------------------------------

    normalized_explanations = []

    if explanations:

        for explanation in explanations:

            # Already a structured Explanation dictionary
            if isinstance(explanation, dict):

                normalized_explanations.append(explanation)

            # If visualization_logic returns a string,
            # convert it into the expected Explanation structure.
            elif isinstance(explanation, str):

                normalized_explanations.append(
                    make_explanation(
                        action="Generate visualization",
                        reason=explanation,
                        alternative_considered="Other suitable chart types",
                        why_not_chosen="The selected visualization was considered more appropriate for the user's question and available data.",
                        expected_impact="Improve understanding of the relevant pattern or relationship in the dataset.",
                        learning_note="Visualization selection is based on the question and characteristics of the uploaded dataset.",
                        confidence="Medium",
                    )
                )

    # --------------------------------------------------------
    # Store explanations
    # --------------------------------------------------------

    state["explanations"] = (
        state.get("explanations", [])
        + normalized_explanations
    )

    # --------------------------------------------------------
    # Format explanations for findings
    # --------------------------------------------------------

    formatted_explanations = format_explanations(
        normalized_explanations
    )

    state["data_findings"] = (
        state.get("data_findings", "")
        + "\n"
        + formatted_explanations
    )

    # --------------------------------------------------------
    # Store agent message
    # --------------------------------------------------------

    state["messages"] = (
        state.get("messages", [])
        + [
            "Visualization Agent: "
            f"generated {len(charts)} chart(s)."
        ]
    )

    return state