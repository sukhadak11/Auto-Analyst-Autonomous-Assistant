import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph_state import AgentState
from llm_config import safe_invoke
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))
from report_formatting import (
    format_analytical_decisions,
    format_educational_insights,
    format_confidence_assessment,
)

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

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

Do NOT write the Analytical Decisions, Educational Insights, or Confidence
Assessment sections yourself — those are added separately after your output,
from real logged data. Stop after Recommendation.
"""


def report_agent_node(state: AgentState) -> AgentState:
    revision_note = ""
    if state.get("critique") and not state.get("approved", True):
        revision_note = f"""IMPORTANT — your previous draft was rejected by the Critic Agent for these reasons:
{state['critique']}
Fix these specific issues in this revision. Do not repeat them."""

    prompt = REPORT_PROMPT.format(
        question=state["question"],
        data_findings=state.get("data_findings", "None provided."),
        research_findings=state.get("research_findings", "None provided."),
        revision_note=revision_note,
    )
    response = safe_invoke(llm, prompt)
    llm_report = response.content

    explanations = state.get("explanations", [])

    full_report = (
        f"{llm_report}\n\n"
        f"**Analytical Decisions**\n\n{format_analytical_decisions(explanations)}\n\n"
        f"**Educational Insights**\n\n{format_educational_insights(explanations)}\n\n"
        f"**Confidence Assessment**\n\n{format_confidence_assessment(explanations)}"
    )

    state["report"] = full_report
    state["revision_count"] = state.get("revision_count", 0) + 1
    state["messages"] = state.get("messages", []) + [f"Report Agent output (revision {state['revision_count']}):\n{full_report}"]
    return state