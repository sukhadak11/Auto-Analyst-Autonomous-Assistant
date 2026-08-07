import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph_state import AgentState
from llm_config import llm, safe_invoke

load_dotenv()

report_llm = ChatGroq(
    model="llama-3.3-70b-versatile",   
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

# report_agent.py
REPORT_PROMPT = """You are the Report Agent. Write a clear, structured
business report answering the original question, using ONLY the findings
provided below. Do not invent numbers, methods, or claims not present in
the findings.

Original question: {question}

Data Agent findings:
{data_findings}

Research Agent findings:
{research_findings}

{revision_note}

Write the report with these sections: Summary, Key Drivers (from data),
Industry Context (from research), Recommendation.
"""

def report_agent_node(state: AgentState) -> AgentState:
    revision_note = ""
    if state.get("critique") and not state.get("approved", True):
     revision_note = f"""IMPORTANT — your previous draft was REJECTED for inventing
methods or claims not present in the source findings:
{state['critique']}

Rules for this revision:
- Do NOT mention any analysis method (regression, time-series, etc.) unless
  it is explicitly named in the source findings below.
- Only state facts that appear word-for-word in spirit in the sources.
- When citing a fact, note whether it came from Data Agent findings or
  Research Agent findings."""
    prompt = REPORT_PROMPT.format(
        question=state["question"],
        data_findings=state.get("data_findings", "None provided."),
        research_findings=state.get("research_findings", "None provided."),
        revision_note=revision_note,
    )
    response = safe_invoke(llm, prompt)
    state["report"] = response.content
    state["revision_count"] = state.get("revision_count", 0) + 1
    state["messages"] = state.get("messages", []) + [f"Report Agent output (revision {state['revision_count']}):\n{response.content}"]
    return state


if __name__ == "__main__":
    test_state: AgentState = {
        "question": "Why might churn be spiking, and how does it compare to industry benchmarks?",
        "plan": [],
        "data_findings": "Contract type and tenure were the top churn drivers based on SHAP analysis.",
        "research_findings": "Industry average churn rate for telecom is roughly 15-25% annually.",
        "report": "",
        "messages": [],
    }
    result = report_agent_node(test_state)
    print("\n=== FINAL REPORT ===\n")
    print(result["report"])