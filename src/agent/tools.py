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


# =========================================================
# Tavily Configuration
# =========================================================

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = (
    TavilyClient(api_key=TAVILY_API_KEY)
    if TAVILY_API_KEY
    else None
)


# =========================================================
# Vector Database Configuration
# =========================================================

PERSIST_DIR = "data/chroma_db"

_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={
        "local_files_only": True
    },
)

_vectordb = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=_embeddings,
)


# =========================================================
# Web Search Tool
# =========================================================

@tool
def search_tool(query: str) -> str:
    """
    Searches the web for current outside context such as
    competitor information, industry benchmarks, news,
    or other information not contained in the user's dataset.

    If the external search service is unavailable, the tool
    returns a graceful message instead of failing the pipeline.

    Args:
        query: Plain web search query.
    """

    if not tavily_client:

        return (
            "External web research is currently unavailable "
            "because the Tavily API key is not configured. "
            "Continue the analysis without external web context."
        )

    try:

        response = tavily_client.search(
            query=query,
            max_results=1,
        )

        results = response.get(
            "results",
            [],
        )

        if not results:

            return "No external web results found."

        formatted_results = []

        for result in results:

            url = result.get(
                "url",
                "Unknown source",
            )

            content = result.get(
                "content",
                "",
            )

            formatted_results.append(
                f"Source: {url}\n"
                f"{content[:500]}"
            )

        return "\n\n".join(
            formatted_results
        )

    except Exception as e:

        return (
            "External web research is currently unavailable. "
            "The search service could not be reached. "
            "Continue the analysis using the available "
            "dataset and internal context."
        )


# =========================================================
# Internal Document Retrieval Tool
# =========================================================

@tool
def retrieve_documents(query: str) -> str:
    """
    Searches the company's internal documents for relevant
    context such as previous reports and policy notes.

    Args:
        query: What to look for in internal documents.
    """

    try:

        docs = _vectordb.similarity_search(
            query,
            k=1,
        )

        if not docs:

            return (
                "No relevant internal documents found."
            )

        formatted_results = []

        for document in docs:

            source = document.metadata.get(
                "source",
                "unknown",
            )

            content = document.page_content[:500]

            formatted_results.append(
                f"Source: {source}\n"
                f"{content}"
            )

        return "\n\n".join(
            formatted_results
        )

    except Exception:

        return (
            "Internal document retrieval is currently "
            "unavailable. Continue the analysis without "
            "internal document context."
        )