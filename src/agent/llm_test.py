from langchain_groq import ChatGroq
import os

llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

print(llm.invoke("Hello"))