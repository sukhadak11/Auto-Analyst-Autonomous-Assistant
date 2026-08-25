# src/agent/tools.py
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from tavily import TavilyClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

PERSIST_DIR = "data/chroma_db"
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"local_files_only": True},
)
_vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=_embeddings)


@tool
def search_tool(query: str) -> str:
    """
    Searches the web for current, outside context — competitor info,
    industry benchmarks, news, or anything not contained in the user's
    own dataset. Pass a plain search query string.

    Args:
        query: the search query, e.g. "average telecom churn rate 2026"
    """
    response = tavily_client.search(query=query, max_results=1)
    results = response.get("results", [])
    formatted = "\n\n".join(
        f"Source: {r['url']}\n{r['content'][:150]}" for r in results
    )
    return formatted if formatted else "No results found."


@tool
def retrieve_documents(query: str) -> str:
    """
    Searches the company's own internal documents (past reports, policy
    notes) for relevant context. Use this for internal knowledge — different
    from search_tool, which searches the live web for outside/industry info.

    Args:
        query: what to look for, e.g. "past analysis findings"
    """
    docs = _vectordb.similarity_search(query, k=1)
    if not docs:
        return "No relevant internal documents found."
    formatted = "\n\n".join(
        f"Source: {d.metadata.get('source', 'unknown')}\n{d.page_content[:150]}"
        for d in docs
    )
    return formatted