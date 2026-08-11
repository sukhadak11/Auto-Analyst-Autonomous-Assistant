# tools.py — top of file, in this exact order
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from tavily import TavilyClient
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from clean import clean_pipeline
from train import train_and_evaluate
from evaluate import (
    load_model_and_data,
    describe_dataset,
    explain_global,
    explain_one_prediction,
)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

PERSIST_DIR = "data/chroma_db"
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"local_files_only": True},
)
_vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=_embeddings)


def get_target_col() -> str:
    """Reads the target column for the CURRENT job, set by the API at upload time."""
    return os.environ.get("AUTOANALYST_TARGET_COL", "churn")


def get_raw_path() -> str:
    """Reads the raw dataset path for the CURRENT job, set by the API at upload time."""
    return os.environ.get("AUTOANALYST_RAW_PATH", "data/telecommunications_churn.csv")


@tool
def run_data_cleaning() -> str:
    """Clean the uploaded dataset. Takes NO arguments — the file path and
target column are already configured internally. Do not pass any arguments."""
    target_col = get_target_col()
    raw_path = get_raw_path()
    df = clean_pipeline(target_col=target_col, raw_path=raw_path)
    return f"Cleaned data saved successfully. Shape: {df.shape[0]} rows, {df.shape[1]} columns. Target column: {target_col}"

@tool
def run_model_training() -> str:
    """Train a model on the cleaned dataset using the configured target column."""
    target_col = get_target_col()
    model, X_test, y_test = train_and_evaluate(target_col=target_col)
    return f"Model trained and saved. Test set size: {len(X_test)} rows."


@tool
def run_shap_explanation(row_index: int = 0) -> str:
    """Generate SHAP explanations for the trained model using the configured target column."""
    target_col = get_target_col()
    model, X, y = load_model_and_data(target_col)
    describe_dataset(X, y, target_col)
    explainer, explanation = explain_global(model, X)
    explain_one_prediction(explainer, X, row_index=row_index)
    return f"SHAP plots saved to data/plots/ for row {row_index}."


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