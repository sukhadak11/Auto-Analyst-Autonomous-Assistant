# src/agent/planner.py

import sys
from pathlib import Path

# src/agent/planner.py -> project root
sys.path.append(str(Path(__file__).resolve().parents[2]))

import json

from graph_state import AgentState
from llm_config import llm, safe_invoke


AVAILABLE_AGENTS = {
    "profiling": (
        "Always required. Detects the target column, dataset type, "
        "identifier columns, data types, and basic dataset characteristics."
    ),

    "cleaning": (
        "Always required. Handles missing values, duplicates, outliers, "
        "data quality issues, and class imbalance when appropriate."
    ),

    "feature_selection": (
        "Checks for redundant or highly correlated features and applies "
        "feature-selection or dimensionality-reduction techniques when "
        "appropriate for the analysis."
    ),

    "model_training": (
        "Trains and compares predictive models when the question involves "
        "prediction, classification, regression, risk, drivers, factors "
        "influencing an outcome, or explaining an outcome."
    ),

    "statistics": (
        "Provides statistical summaries, distributions, correlations, "
        "relationships, comparisons, and numerical insights when these "
        "would help answer the user's question."
    ),

    "visualization": (
        "Analyzes the user's question and the actual uploaded dataset to "
        "automatically select and generate suitable visualizations. It must "
        "determine the relevant columns and appropriate chart types from "
        "the data rather than relying on predefined dataset-specific rules."
    ),

    "time_series": (
        "Handles time-based trend analysis, seasonality, and forecasting. "
        "Use ONLY when the dataset is identified as time-series data."
    ),

    "research": (
        "Searches the web and internal documents for external context, "
        "benchmarks, industry comparisons, or supporting information."
    ),

    "report": (
        "Always required. Synthesizes findings from all selected agents "
        "into the final report."
    ),
}


PLANNER_PROMPT = """
You are the planning agent for a generic automated data-analysis system.

The system can receive ANY uploaded dataset from ANY business domain.
Do not assume a specific dataset, industry, target column, or column name.

Your task is to determine which analysis agents are required to answer the
user's question effectively.

========================
HARD RULES
========================

1. ALWAYS include:
   - profiling
   - cleaning
   - report

2. MODEL TRAINING:

   Include model_training when the question involves:
   - prediction
   - classification
   - regression
   - risk
   - forecasting
   - factors influencing an outcome
   - drivers of an outcome
   - explaining why an outcome occurs
   - identifying important features associated with an outcome

   Do not require model_training for purely descriptive questions where
   prediction or outcome explanation is clearly unnecessary.

3. STATISTICS:

   Include statistics when the question asks for or would materially
   benefit from:
   - statistical relationships
   - correlations
   - distributions
   - numerical summaries
   - comparisons
   - patterns
   - relationships between variables
   - segment-level statistical analysis

4. VISUALIZATION:

   Include visualization when:

   - The user explicitly requests a visualization, chart, plot, graph,
     visual analysis, or similar output.

   OR

   - The user asks to generate:
       * relevant visualizations
       * suitable visualizations
       * appropriate visualizations
       * useful visualizations
       * visualizations based on the findings

   OR

   - The user asks for trends, comparisons, distributions, relationships,
     rankings, patterns, segment differences, or other findings where a
     visual representation would materially improve understanding.

   OR

   - The user asks for a complete analysis and explicitly expects the
     important findings to be communicated visually.

   IMPORTANT:
   Visualization selection must NOT depend on specific dataset names,
   business domains, or hardcoded column names.

   The Visualization Agent will inspect the actual uploaded dataset and
   determine:
   - which columns are relevant
   - their data types
   - whether they represent categories, numerical values, dates, etc.
   - what relationship should be visualized
   - which chart type is most appropriate

   The planner should only decide whether visualization is needed.
   It should NOT decide the exact chart or column.

5. TIME SERIES:

   Include time_series ONLY when dataset_type is exactly:
   "time_series".

   Never select time_series based only on the wording of the question.

6. RESEARCH:

   Include research when external context, benchmarks, industry
   information, or supporting external evidence would improve the answer.

========================
AVAILABLE AGENTS
========================

{agent_descriptions}

========================
INPUT
========================

Business question:
{question}

Dataset type:
{dataset_type}

========================
OUTPUT
========================

Return ONLY a valid JSON list containing the names of the required agents.

Do not return explanations.
Do not return markdown.
Do not return additional text.
"""


def plan_node(state: AgentState) -> AgentState:
    """
    Determine which agents are required for the current user question.

    The planner is dataset-agnostic. It decides whether visualization is
    required, while the Visualization Agent decides which columns and
    chart types should actually be used.
    """

    agent_descriptions = "\n".join(
        f"- {name}: {description}"
        for name, description in AVAILABLE_AGENTS.items()
    )

    prompt = PLANNER_PROMPT.format(
        agent_descriptions=agent_descriptions,
        question=state["question"],
        dataset_type=state.get("dataset_type", "unknown"),
    )

    response = safe_invoke(llm, prompt)

    try:
        content = response.content.strip()

        # Handle accidental markdown code fences from the LLM.
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        required = json.loads(content)

        # Ensure the result is actually a list.
        if not isinstance(required, list):
            raise ValueError("Planner response is not a list.")

        # Keep only known agents.
        required = [
            agent
            for agent in required
            if agent in AVAILABLE_AGENTS
        ]

    except (json.JSONDecodeError, ValueError, TypeError):
        # Safe fallback.
        required = [
            "profiling",
            "cleaning",
            "feature_selection",
            "model_training",
            "research",
            "report",
        ]

    # -----------------------------------------
    # Mandatory agents
    # -----------------------------------------

    for always_needed in [
        "profiling",
        "cleaning",
        "report",
    ]:
        if always_needed not in required:
            required.append(always_needed)

    # -----------------------------------------
    # Time-series safety rule
    # -----------------------------------------

    if (
        state.get("dataset_type") != "time_series"
        and "time_series" in required
    ):
        required.remove("time_series")

    # -----------------------------------------
    # Store planner decision
    # -----------------------------------------

    state["required_agents"] = required

    state["plan"] = [
        f"Selected agents: {', '.join(required)}"
    ]

    state["messages"] = (
        state.get("messages", [])
        + [f"Planner selected agents: {required}"]
    )

    return state


# ---------------------------------------------------------
# Manual planner tests
# ---------------------------------------------------------

if __name__ == "__main__":

    test_cases = [

        {
            "name": "Action / prediction",
            "question": (
                "What action should we take when the model predicts an outcome?"
            ),
            "dataset_type": "tabular",
        },

        {
            "name": "Statistical relationships",
            "question": (
                "What statistical relationships exist between the variables?"
            ),
            "dataset_type": "tabular",
        },

        {
            "name": "Explicit visualization",
            "question": (
                "Show me suitable charts for the important findings."
            ),
            "dataset_type": "tabular",
        },

        {
            "name": "Relevant visualizations",
            "question": (
                "Generate relevant visualizations based on the dataset "
                "and the important findings."
            ),
            "dataset_type": "tabular",
        },

        {
            "name": "Trend",
            "question": (
                "Show the trend over time and explain the important changes."
            ),
            "dataset_type": "time_series",
        },

        {
            "name": "Complete analysis",
            "question": (
                "Perform a complete analysis of the uploaded dataset. "
                "Identify important patterns, relationships, segment "
                "differences, and generate suitable visualizations."
            ),
            "dataset_type": "tabular",
        },
    ]

    for test in test_cases:

        state = {
            "question": test["question"],
            "dataset_type": test["dataset_type"],
            "messages": [],
        }

        result = plan_node(state)

        print(f"\n{test['name']}")
        print("-" * 60)
        print(result["required_agents"])