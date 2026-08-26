# src/agent/llm_config.py
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from groq import RateLimitError, APIStatusError, NotFoundError

# Explicitly locate .env relative to this file, not the cwd
env_path = Path(__file__).resolve().parents[2] / ".env"  # adjust levels as needed
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError(
        f"GROQ_API_KEY not found. Looked for .env at: {env_path}. "
        "Make sure the .env file exists and contains GROQ_API_KEY=..."
    )

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=api_key,
    temperature=0,
)

def safe_invoke(llm, prompt, max_retries=3):
    last_exception = None
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)

            if response is None:
                raise ValueError("LLM/agent returned None")

            # react agents return a dict like {"messages": [...]}
            if isinstance(response, dict):
                if not response.get("messages"):
                    raise ValueError(f"Agent returned no messages: {response!r}")
            # normal chat models return an object with .content
            elif getattr(response, "content", None) is None:
                raise ValueError(f"LLM returned empty/invalid response: {response!r}")

            return response
        except (RateLimitError, APIStatusError) as e:
            last_exception = e
            logging.warning(f"Attempt {attempt+1}/{max_retries} failed (API error): {type(e).__name__}: {e}")
            time.sleep(11)
        except Exception as e:
            last_exception = e
            logging.warning(f"Attempt {attempt+1}/{max_retries} failed: {type(e).__name__}: {e}")
            time.sleep(5)

    raise RuntimeError(f"Exceeded max retry attempts. Last error: {last_exception}") from last_exception