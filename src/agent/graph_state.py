# src/agent/graph_state.py
from typing import TypedDict, List, Annotated
import operator
from explanation_schema import Explanation


class AgentState(TypedDict):

    # User request
    question: str

    # Planner
    plan: List[str]
    required_agents: List[str]

    # Analysis findings
    data_findings: str
    research_findings: str
    report: str
    critique: str

    # Critic / human approval
    approved: bool
    revision_count: int
    human_decision: str
    human_notes: str

    # Explanations
    explanations: List[Explanation]

    # Dataset paths
    raw_path: str
    clean_path: str

    # Dataset information
    target_col: str
    dataset_type: str
    id_cols: List[str]

    # Interpretability
    needs_interpretability: bool

    # Model information
    model_path: str
    model_name: str
    feature_importance: List[tuple]

    # Job
    job_id: str

    # Dynamically generated visualizations
    generated_charts: List[dict]

    # LangGraph messages
    messages: Annotated[list, operator.add]