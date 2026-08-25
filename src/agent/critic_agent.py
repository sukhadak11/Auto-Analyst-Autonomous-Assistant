# critic_agent.py
import os
from langchain_groq import ChatGroq
from src.agent.graph_state import AgentState
from llm_config import llm, safe_invoke
critic_llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

CRITIC_PROMPT = """You are a Critic Agent. Check the report below against the
source findings. Flag ONLY claims that contradict the source findings or
introduce a specific method/number that does not appear anywhere in the
sources.

Do NOT flag:
- Paraphrasing of information that IS present in the sources, even if reworded
- Where in the report a true fact appears (e.g. mentioned in one section vs another)
- Missing extra analysis or elaboration the report doesn't provide
- Organizational or structural choices

ONLY flag a real fabrication: a specific number, method, or claim that does
NOT appear anywhere in the source findings below, or directly contradicts them.

Source — Data Agent findings:
{data_findings}

Source — Research Agent findings:
{research_findings}

Report to review:
{report}

Respond in EXACTLY this format:
VERDICT: APPROVED
or
VERDICT: NEEDS_REVISION
ISSUES: (only genuine fabrications or contradictions)
"""

def critic_node(state: AgentState) -> AgentState:
    prompt = CRITIC_PROMPT.format(
        data_findings=state.get("data_findings", "None provided."),
        research_findings=state.get("research_findings", "None provided."),
        report=state.get("report", ""),
    )
    response = safe_invoke(critic_llm, prompt)   # <-- use critic_llm, not the shared 8B llm
    content = response.content.strip()

    content_upper = content.upper()
    if "NEEDS_REVISION" in content_upper:
        approved = False
    elif "VERDICT: APPROVED" in content_upper:
        approved = True
    else:
        approved = False

    state["critique"] = content
    state["approved"] = approved
    state["messages"] = state.get("messages", []) + [f"Critic Agent verdict:\n{content}"]
    return state