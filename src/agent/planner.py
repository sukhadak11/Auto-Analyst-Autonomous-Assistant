import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.agent.graph_state import AgentState
from llm_config import llm, safe_invoke
load_dotenv()


PLANNER_PROMPT = """You are a planning agent for a business analytics system.
Given a business question, break it into sub-tasks. Available capabilities:
- DATA_AGENT can only: clean the dataset, train a churn prediction model, and
  generate SHAP feature-importance explanations. It cannot forecast future
  rates and has no access to complaints, tickets, or billing records.
- RESEARCH_AGENT can search the web and internal documents for outside context.
- REPORT_AGENT writes the final report from what the other two produce.

Only propose sub-tasks that match these actual capabilities.

Business question: {question}
Respond with a numbered list of sub-tasks only.
"""

def plan_node(state: AgentState) -> AgentState:
    prompt = PLANNER_PROMPT.format(question=state["question"])
    response = safe_invoke(llm, prompt)   
    plan_lines = [line.strip() for line in response.content.split("\n") if line.strip()]
    state["plan"] = plan_lines
    state["messages"] = state.get("messages", []) + [f"Planner created plan:\n{response.content}"]
    return state
