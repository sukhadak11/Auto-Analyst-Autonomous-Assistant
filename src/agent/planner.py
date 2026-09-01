import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))  # src/agent/planner.py -> project root

import json
from graph_state import AgentState
from llm_config import llm, safe_invoke

AVAILABLE_AGENTS = {
    "profiling": "Always required. Detects target column, dataset type, ID columns.",
    "cleaning": "Always required. Handles missing values, duplicates, outliers, class imbalance.",
    "feature_selection": "Checks for redundant features and applies PCA if appropriate. Usually required for tabular ML tasks.",
    "model_training": "Trains and compares predictive models. Required when the question asks about prediction, drivers, or classification/regression.",
    "statistics": "Provides statistical summaries, correlations, distributions, hypothesis-style insights. Use when the question asks about patterns, relationships, or 'how much/many' style statistical questions.",
    "visualization": "Selects and describes useful charts for communicating findings. Use when the question would benefit from visual explanation, or explicitly asks to 'show' or 'visualize'.",
    "time_series": "Handles trend analysis, seasonality, forecasting. ONLY relevant if the dataset is time-series (checked separately, not by question alone).",
    "research": "Searches the web and internal documents for outside context, benchmarks, industry comparisons.",
    "report": "Always required. Synthesizes everything into the final report.",
}

PLANNER_PROMPT = """You are a planning agent for a business analytics system.
Given a business question and the dataset type, decide which of the following
agents are needed.

HARD RULES:
- profiling, cleaning, and report are ALWAYS required — do not omit them.
- model_training should be included unless the question EXPLICITLY has
  nothing to do with predicting or explaining an outcome (e.g. pure data
  description with no target-related question at all). Most business
  questions about "why X happens" or "what drives X" DO need model_training.
- time_series should ONLY be included if dataset_type is "time_series".
- statistics should ONLY be included if the question explicitly asks about
  statistical relationships, correlations, distributions, or "how much/many"
  style comparisons — not just because the topic sounds analytical.
- visualization should ONLY be included if the question explicitly asks to
  "show", "visualize", "chart", "plot", or "graph" something.

Available agents:
{agent_descriptions}

Business question: {question}
Dataset type: {dataset_type}

Respond with ONLY a JSON list of agent names needed, nothing else.
"""

def plan_node(state: AgentState) -> AgentState:
    agent_descriptions = "\n".join(f"- {name}: {desc}" for name, desc in AVAILABLE_AGENTS.items())
    prompt = PLANNER_PROMPT.format(
        agent_descriptions=agent_descriptions,
        question=state["question"],
        dataset_type=state.get("dataset_type", "unknown"),
    )

    response = safe_invoke(llm, prompt)

    try:
        required = json.loads(response.content.strip())
    except (json.JSONDecodeError, ValueError):
        required = ["profiling", "cleaning", "feature_selection", "model_training", "research", "report"]

    for always_needed in ["profiling", "cleaning", "report"]:
        if always_needed not in required:
            required.append(always_needed)
    if state.get("dataset_type") != "time_series" and "time_series" in required:
        required.remove("time_series")

    state["required_agents"] = required
    state["plan"] = [f"Selected agents: {', '.join(required)}"]
    state["messages"] = state.get("messages", []) + [f"Planner selected agents: {required}"]
    return state


if __name__ == "__main__":
    state1 = {"question": "What action should we take when the model predicts churn?", "dataset_type": "tabular"}
    r1 = plan_node(state1)
    print("Test 1:", r1["required_agents"])

    state2 = {"question": "What statistical relationships exist between usage patterns and churn?", "dataset_type": "tabular"}
    r2 = plan_node(state2)
    print("Test 2:", r2["required_agents"])

    state3 = {"question": "Show me a chart comparing churn rates across customer segments.", "dataset_type": "tabular"}
    r3 = plan_node(state3)
    print("Test 3:", r3["required_agents"])

    state4 = {"question": "What is the trend in churn over time?", "dataset_type": "tabular"}
    r4 = plan_node(state4)
    print("Test 4:", r4["required_agents"])