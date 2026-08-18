import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from llm_config import llm

from tools import all_tools  

load_dotenv()


agent = create_react_agent(llm, all_tools)


def ask(question: str):
    result = agent.invoke({"messages": [("user", question)]})
    final_message = result["messages"][-1]
    print("\n=== FINAL ANSWER ===")
    print(final_message.content)
    return result

'''
if __name__ == "__main__":
    ask(
        "Why might churn be spiking? Clean the data, train a model, "
        "explain what's driving churn, and check how our churn rate "
        "compares to typical telecom industry benchmarks."
    )
    '''