import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph_state import AgentState
from llm_config import safe_invoke
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "pipeline"))

from src.pipeline.report_formatting import (
    format_analytical_decisions,
    format_confidence_assessment,
)

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

REPORT_PROMPT = """You are the Report Agent. Answer the user's question directly
and briefly using ONLY the findings below. Never invent numbers, methods, or
claims not present in the findings.

CRITICAL RULE: If the question asks about a SPECIFIC individual, customer, or
record (e.g. gives specific feature values and asks "will THIS customer churn"),
and no per-instance prediction result appears in the findings below, you MUST
say exactly: "A specific prediction for this individual was not computed in
this analysis; only the model's aggregate performance on the full dataset is
available." Do NOT invent a risk score, probability, or individual assessment.

User's question: {question}

Data findings: {data_findings}
Top feature drivers: {feature_importance_summary}
Research findings: {research_findings}
Per-instance prediction (if computed): {prediction_result}

{revision_note}

Write ONLY these two sections, each 2-4 sentences maximum:
1. Answer — direct answer to the question, naming real drivers/numbers if available.
2. Recommendation — 2-3 concrete, specific actions tied to the actual drivers found.

Do not write more than 150 words total. Do not repeat the findings verbatim —
synthesize them.
"""

def report_agent_node(state: AgentState) -> AgentState:
    revision_note = ""
    if state.get("critique") and not state.get("approved", True):
        revision_note = f"""IMPORTANT — your previous draft was rejected by the Critic Agent.

Critic feedback:
{state['critique']}

Revise the report and specifically address every issue identified by the Critic Agent.
Do not ignore the feedback."""

    feature_importance = state.get("feature_importance", [])
    if feature_importance:
        feature_importance_summary = "\n".join(
            f"{name}: {float(val):.3f}" for name, val in feature_importance[:5]
        )
    else:
        feature_importance_summary = (
            "No feature importance data is available. "
            "Do not claim that SHAP feature drivers were successfully generated."
        )

    research_findings = state.get("research_findings", "")
    prediction_result = state.get("prediction_result", "Not computed in this analysis.")


    prompt = REPORT_PROMPT.format(
        question=state.get("question", "Analyze this dataset and summarize the key findings."),
        data_findings=state.get("data_findings", "None provided."),
        feature_importance_summary=feature_importance_summary,
        research_findings=research_findings or "None provided.",
        prediction_result=prediction_result,
        revision_note=revision_note,
    )

    response = safe_invoke(llm.bind(max_tokens=2500), prompt)
    llm_report = response.content.strip()

    explanations = state.get("explanations", [])
    analytical_decisions = format_analytical_decisions(explanations)
    confidence_assessment = format_confidence_assessment(explanations)

    full_report = (
        f"{llm_report}\n\n"
        f"**Key Decisions**\n"
        f"{analytical_decisions}\n\n"
        f"**Confidence Summary**\n"
        f"{confidence_assessment}"
    )

    state["report"] = full_report
    state["revision_count"] = state.get("revision_count", 0) + 1
    state["messages"] = state.get("messages", []) + [
        f"Report Agent output (revision {state['revision_count']}):\n{full_report}"
    ]
    return state