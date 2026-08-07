import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from graph_state import AgentState
from tools import run_data_cleaning, run_model_training, run_shap_explanation
from llm_config import llm
from llm_config import safe_invoke

# IMPORTANT: use the correct import for your installed package
from langgraph.prebuilt import create_react_agent

load_dotenv()

print("DEBUG: starting script")

groq_key = os.getenv("GROQ_API_KEY")
print("DEBUG: GROQ key loaded:", bool(groq_key))


print("DEBUG: LLM created")

data_tools = [run_data_cleaning, run_model_training, run_shap_explanation]
print("DEBUG: tools loaded")

data_react_agent = create_react_agent(llm, data_tools)
print("DEBUG: agent created")

DATA_AGENT_PROMPT = """You are the Data Agent. Your job is limited to the
company's own dataset: clean it, train a model, and explain what drives the
outcome using SHAP.

CRITICAL RULES:
- Call run_data_cleaning, then run_model_training, then run_shap_explanation — each
  takes NO arguments.
- After the tools run, summarize ONLY the exact numbers and messages the tools
  returned (e.g. rows/columns cleaned, test set size, ROC-AUC if shown, which
  plots were saved).
- Do NOT forecast future churn rates. Do NOT invent percentages. Do NOT mention
  billing issues, service outages, or customer complaints — this dataset has no
  such columns, and no tool analyzes complaints or tickets.
- If you don't have a specific number from a tool result, do not state one.

Task from the plan: {task}
"""
def data_agent_node(state: AgentState) -> AgentState:
    print("DEBUG: entered data_agent_node")
    print("DEBUG: incoming state =", state)

    relevant_tasks = [t for t in state["plan"] if "DATA_AGENT" in t]
    task_text = "\n".join(relevant_tasks) if relevant_tasks else "Run the full data pipeline and explain key drivers."

    print("DEBUG: about to invoke agent")

    prompt = DATA_AGENT_PROMPT.format(task=task_text)
    print("DEBUG: prompt =", prompt)

    result = safe_invoke(data_react_agent, {"messages": [("user", prompt)]})

    print("DEBUG: agent invoke returned")
    print("DEBUG: raw result =", result)

    findings = result["messages"][-1].content

    state["data_findings"] = findings
    state["messages"] = state.get("messages", []) + [f"Data Agent findings:\n{findings}"]
    return state


if __name__ == "__main__":
    print("DEBUG: inside main")

    test_state = {
        "plan": ["DATA_AGENT: Clean the data, train the model, and explain key drivers."],
        "messages": [],
        "data_findings": ""
    }

    try:
        output_state = data_agent_node(test_state)
        print("\n=== FINAL STATE ===")
        print(output_state)
    except Exception as e:
        print("ERROR:", repr(e))