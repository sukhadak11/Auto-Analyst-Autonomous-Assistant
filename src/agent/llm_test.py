import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from llm_config import llm

load_dotenv()


if __name__ == "__main__":
    response = llm.invoke("Say hello and confirm you're working.")
    print(response.content)