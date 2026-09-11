# src/agent/research_agent.py

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from dotenv import load_dotenv

load_dotenv()

from langgraph.prebuilt import create_react_agent

from graph_state import AgentState
from tools import search_tool, retrieve_documents
from llm_config import llm, safe_invoke


# =========================================================
# Research Agent
# =========================================================

research_tools = [
    search_tool,
    retrieve_documents,
]

research_react_agent = create_react_agent(
    llm,
    research_tools,
)


RESEARCH_AGENT_PROMPT = """
You are the Research Agent.

Your responsibility is to find useful external or internal
context that can improve the analysis.

Use:
- Web search for industry benchmarks, competitor information,
  recent developments, or other external context.
- Internal document retrieval for relevant company documents.

Do not analyze the user's dataset directly.

External research is optional. If web search is unavailable,
continue using available internal context and do not treat the
unavailability as a pipeline failure.

Do not invent facts or external sources.

Task:
{task}
"""


# =========================================================
# Research Node
# =========================================================

def research_agent_node(
    state: AgentState,
) -> AgentState:

    relevant_tasks = [
        task
        for task in state.get("plan", [])
        if "RESEARCH_AGENT" in task
    ]

    task_text = (
        "\n".join(relevant_tasks)
        if relevant_tasks
        else (
            "Find relevant industry context for this question: "
            + state.get("question", "")
        )
    )

    prompt = RESEARCH_AGENT_PROMPT.format(
        task=task_text
    )

    try:

        result = safe_invoke(
            research_react_agent,
            {
                "messages": [
                    ("user", prompt)
                ]
            },
        )

        messages = result.get(
            "messages",
            [],
        )

        if messages:

            findings = messages[-1].content

        else:

            findings = (
                "No research findings were returned."
            )

    except Exception as e:

        findings = (
            "External research was unavailable during this "
            "analysis. The remaining analysis was completed "
            "using the available dataset and other agents."
        )

    state["research_findings"] = findings

    state["messages"] = (
        state.get("messages", [])
        + [
            "Research Agent findings:\n"
            + findings
        ]
    )

    return state