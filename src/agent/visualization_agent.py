import pandas as pd
from pathlib import Path
import sys

from graph_state import AgentState

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "pipeline"
    )
)

from visualization_logic import (
    select_and_generate_visualizations
)


def visualization_agent_node(
    state: AgentState,
) -> AgentState:
    """
    Generate visualizations from the cleaned dataset.

    The Visualization Agent:
    1. Loads the cleaned dataset.
    2. Passes the real dataset to visualization logic.
    3. Generates appropriate charts.
    4. Stores JSON-safe chart metadata in generated_charts.
    5. Stores explanations in the agent state.
    """

    clean_path = state.get(
        "clean_path",
        "data/clean_data.csv",
    )

    target_col = state.get(
        "target_col"
    )

    job_id = state.get(
        "job_id",
        "manual_test",
    )

    question = state.get(
        "question",
        "",
    )

    clean_file = Path(
        clean_path
    )

    # --------------------------------------------------------
    # Validate cleaned dataset
    # --------------------------------------------------------

    if not clean_file.exists():

        message = (
            "Visualization Agent could not find "
            f"the cleaned dataset: {clean_file}"
        )

        state["generated_charts"] = []

        state["messages"] = (
            state.get("messages", [])
            + [message]
        )

        state["data_findings"] = (
            state.get("data_findings", "")
            + "\n"
            + message
        )

        return state

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            clean_file
        )

    except Exception as e:

        message = (
            "Visualization Agent could not read "
            f"the cleaned dataset: {e}"
        )

        state["generated_charts"] = []

        state["messages"] = (
            state.get("messages", [])
            + [message]
        )

        state["data_findings"] = (
            state.get("data_findings", "")
            + "\n"
            + message
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
                    [],
                ),
                job_id=job_id,
                output_dir="data/plots",
            )
        )

    except Exception as e:

        message = (
            "Visualization Agent encountered an error "
            f"while generating charts: {e}"
        )

        state["generated_charts"] = []

        state["messages"] = (
            state.get("messages", [])
            + [message]
        )

        state["data_findings"] = (
            state.get("data_findings", "")
            + "\n"
            + message
        )

        return state

    # --------------------------------------------------------
    # Normalize chart metadata
    # --------------------------------------------------------

    normalized_charts = []

    for chart in charts:

        # Expected format:
        # {
        #     "chart_type": "...",
        #     "filename": "..."
        # }

        if isinstance(chart, dict):

            filename = (
                chart.get("filename")
                or chart.get("file")
                or chart.get("name")
            )

            chart_type = (
                chart.get("chart_type")
                or "visualization"
            )

            if filename:

                normalized_charts.append(
                    {
                        "chart_type": str(
                            chart_type
                        ),
                        "filename": str(
                            filename
                        ),
                    }
                )

        # Backward compatibility:
        # ("chart_type", "path")
        elif isinstance(chart, (tuple, list)):

            if len(chart) >= 2:

                chart_type = chart[0]
                chart_path = chart[1]

                filename = Path(
                    str(chart_path)
                ).name

                normalized_charts.append(
                    {
                        "chart_type": str(
                            chart_type
                        ),
                        "filename": filename,
                    }
                )

        # Backward compatibility:
        # plain filename/path
        elif chart:

            filename = Path(
                str(chart)
            ).name

            normalized_charts.append(
                {
                    "chart_type": "visualization",
                    "filename": filename,
                }
            )

    # --------------------------------------------------------
    # Remove duplicate charts
    # --------------------------------------------------------

    unique_charts = []

    seen = set()

    for chart in normalized_charts:

        filename = chart.get(
            "filename"
        )

        if (
            filename
            and filename not in seen
        ):

            unique_charts.append(
                chart
            )

            seen.add(
                filename
            )

    normalized_charts = unique_charts

    # --------------------------------------------------------
    # Store charts
    # --------------------------------------------------------

    state["generated_charts"] = (
        normalized_charts
    )

    # --------------------------------------------------------
    # Store explanations safely
    # --------------------------------------------------------

    existing_explanations = state.get(
        "explanations",
        [],
    )

    normalized_explanations = []

    for explanation in explanations:

        if isinstance(
            explanation,
            dict,
        ):

            normalized_explanations.append(
                explanation
            )

        else:

            # Convert legacy string explanations
            # into the Explanation schema.

            normalized_explanations.append(
                {
                    "action": "Visualization decision",
                    "reason": str(
                        explanation
                    ),
                    "alternative_considered": (
                        "No visualization"
                    ),
                    "why_not_chosen": (
                        "A visualization was considered "
                        "useful for the requested analysis."
                    ),
                    "expected_impact": (
                        "Improve understanding of "
                        "the analysis findings."
                    ),
                    "learning_note": (
                        "Visualization selection is based "
                        "on the question and available data."
                    ),
                    "confidence": "Medium",
                }
            )

    state["explanations"] = (
        existing_explanations
        + normalized_explanations
    )

    # --------------------------------------------------------
    # Data findings
    # --------------------------------------------------------

    if normalized_charts:

        chart_names = [
            chart["filename"]
            for chart in normalized_charts
        ]

        finding = (
            "Visualization Agent generated "
            f"{len(normalized_charts)} chart(s): "
            + ", ".join(chart_names)
        )

    else:

        finding = (
            "Visualization Agent did not generate "
            "any suitable charts."
        )

    state["data_findings"] = (
        state.get(
            "data_findings",
            "",
        )
        + "\n"
        + finding
    )

    # --------------------------------------------------------
    # Messages
    # --------------------------------------------------------

    state["messages"] = (
        state.get(
            "messages",
            [],
        )
        + [
            (
                "Visualization Agent: generated "
                f"{len(normalized_charts)} chart(s)."
            )
        ]
    )

    return state