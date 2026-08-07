# src/agent/graph_state.py
from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    question: str                          # original business question
    plan: List[str]                        # sub-tasks the planner creates
    data_findings: str                     # output from Data Agent
    research_findings: str                 # output from Research Agent
    report: str                            # final report from Report Agent
    messages: List[str] 
    critique: str                          # <-- new: critic's feedback
    approved: bool                         # <-- new: "approved" | "rejected" | "needs_revision"   
    human_decision: str      
    human_notes: str              # <-- new: whether critic signed off
    revision_count: int                     # running conversation/log


# quick test
if __name__ == "__main__":
    test_state: AgentState = {
        "question": "Why might churn be spiking?",
        "plan": ["1. DATA_AGENT: clean data, train model, explain churn drivers"],
        "data_findings": "", "research_findings": "", "report": "", "messages": [],
        "critique": "", "approved": False, "revision_count": 0
    }
    print(test_state["data_findings"])