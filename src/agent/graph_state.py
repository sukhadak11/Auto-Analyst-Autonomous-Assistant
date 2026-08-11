# src/agent/graph_state.py
from typing import TypedDict, List, Annotated
import operator

from explanation_schema import Explanation
class AgentState(TypedDict):
    question: str
    plan: List[str]
    data_findings: str
    research_findings: str
    report: str
    critique: str
    approved: bool
    revision_count: int
    human_decision: str
    human_notes: str
    explanations: List[Explanation]   # <-- new: every agent appends here
    messages: Annotated[list, operator.add]

# quick test
if __name__ == "__main__":
    test_state: AgentState = {
        "question": "Why might churn be spiking?",
        "plan": ["1. DATA_AGENT: clean data, train model, explain churn drivers"],
        "data_findings": "", "research_findings": "", "report": "", "messages": [],
        "critique": "", "approved": False, "revision_count": 0
    }
    print(test_state["data_findings"])