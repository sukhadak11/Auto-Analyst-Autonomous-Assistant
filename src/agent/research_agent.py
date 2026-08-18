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

research_tools = [search_tool, retrieve_documents]
research_react_agent = create_react_agent(llm, research_tools)

RESEARCH_AGENT_PROMPT = """Research Agent: find outside context via web search
or internal docs only — industry benchmarks, competitor info, news. Do not
analyze the company's own dataset.

Task: {task}
"""

def research_agent_node(state: AgentState) -> AgentState:
    relevant_tasks = [t for t in state["plan"] if "RESEARCH_AGENT" in t]
    task_text = (
        "\n".join(relevant_tasks)
        if relevant_tasks
        else "Find relevant industry context for this question: " + state["question"]
    )

    prompt = RESEARCH_AGENT_PROMPT.format(task=task_text)

    result = safe_invoke(research_react_agent, {"messages": [("user", prompt)]})   # <-- fixed

    findings = result["messages"][-1].content

    state["research_findings"] = findings
    state["messages"] = state.get("messages", []) + [f"Research Agent findings:\n{findings}"]
    return state

'''
if __name__ == "__main__":
    test_state = {
        "question": "How does our churn risk compare to telecom industry benchmarks?",
        "plan": ["RESEARCH_AGENT: Find telecom churn benchmarks and recent industry context."],
        "messages": [],
        "research_findings": ""
    }
    output = research_agent_node(test_state)
    print("\n=== FINAL STATE ===")
    print(output)
    '''