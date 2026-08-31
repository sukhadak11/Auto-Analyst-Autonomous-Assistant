
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
    format_educational_insights,
    format_confidence_assessment,
)

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)


REPORT_PROMPT = """You are the Report Agent for an autonomous data science system.

Your role is to behave like both:
1. A professional Data Scientist who analyzes evidence and gives practical conclusions.
2. A Data Science Mentor who explains why analytical decisions were made and what the user can learn from them.

The user asked a specific business question. Answer it using ONLY the findings provided below. Do not invent facts, numbers, relationships, or recommendations that are not supported by the findings.

User's question:
{question}

Data Agent findings:
{data_findings}

Top model feature drivers:
{feature_importance_summary}

Research Agent findings:
{research_findings}

{revision_note}

IMPORTANT WRITING REQUIREMENTS:

- Keep the content in paragraphs.
- Do NOT use markdown tables.
- Do NOT use bullet-point lists.
- Do NOT use numbered lists.
- Do NOT return JSON.
- Do NOT repeat the same information unnecessarily.
- Keep each section logically separated with a heading.
- Use complete sentences.
- Mention actual feature names and numerical values when they are available.
- Do not describe SHAP as available if no SHAP feature importance was successfully generated.
- If a section has insufficient evidence, state that clearly instead of inventing information.

Write the report using exactly these sections and order:

Direct Answer

Write 2-4 sentences directly answering the user's question. Mention the most important findings and the strongest available feature drivers when feature importance data is available.

Recommended Actions

Write this section as one or more connected paragraphs. Each recommendation must be tied to an actual feature or finding from the analysis. Explain what should be done and why. Avoid generic recommendations.

Supporting Data

Write a paragraph explaining the selected model, its performance score, dataset characteristics, and important data-quality findings. Include numerical values when available.

Industry Context

Include this section ONLY when meaningful research findings are provided. Explain the relevant industry context in paragraph form and connect it to the dataset findings. Do not introduce unsupported claims.

The final response must be complete and must not end in the middle of a sentence.
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
            f"{name}: {float(val):.3f}"
            for name, val in feature_importance[:5]
        )
    else:
        feature_importance_summary = (
            "No feature importance data is available. "
            "Do not claim that SHAP feature drivers were successfully generated."
        )

    research_findings = state.get("research_findings", "")

    prompt = REPORT_PROMPT.format(
        question=state.get(
            "question",
            "Analyze this dataset and summarize the key findings."
        ),
        data_findings=state.get("data_findings", "None provided."),
        feature_importance_summary=feature_importance_summary,
        research_findings=research_findings or "None provided.",
        revision_note=revision_note,
    )

    # Generate the main analytical report.
    response = safe_invoke(
        llm.bind(max_tokens=2500),
        prompt
    )

    llm_report = response.content.strip()

    # ---------------------------------------------------------
    # Structured analytical reasoning
    # ---------------------------------------------------------
    explanations = state.get("explanations", [])

    analytical_decisions = format_analytical_decisions(explanations)
    educational_insights = format_educational_insights(explanations)
    confidence_assessment = format_confidence_assessment(explanations)

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------
    full_report = (
        f"{llm_report}\n\n"
        f"Analytical Decisions\n\n"
        f"{analytical_decisions}\n\n"
        f"Educational Insights\n\n"
        f"{educational_insights}\n\n"
        f"Confidence Assessment\n\n"
        f"{confidence_assessment}"
    )

    state["report"] = full_report

    state["revision_count"] = state.get("revision_count", 0) + 1

    state["messages"] = state.get("messages", []) + [
        f"Report Agent output (revision {state['revision_count']}):\n{full_report}"
    ]

    return state