
import os
import time
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from groq import RateLimitError, APIStatusError, NotFoundError

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)
#tighten wait times for per-minute limits specifically
def safe_invoke(agent_or_llm, input_data, max_attempts=6):
    for attempt in range(max_attempts):
        try:
            return agent_or_llm.invoke(input_data)
        except NotFoundError as e:
            raise RuntimeError(f"Model not found — check your model string is still valid: {e}")
        except (RateLimitError, APIStatusError) as e:
            msg = str(e)
            if "tokens per day" in msg.lower() or "TPD" in msg:
                raise RuntimeError(f"Daily quota exhausted:\n{msg}")
            match = __import__("re").search(r"try again in ([\d.]+)(ms|s|m)", msg)
            if match:
                value, unit = float(match.group(1)), match.group(2)
                wait_seconds = value / 1000 if unit == "ms" else value * 60 if unit == "m" else value
            else:
                wait_seconds = 10
            wait_seconds = min(max(wait_seconds, 2) + 1, 30)
            print(f"Waiting {wait_seconds:.1f}s...")
            import time; time.sleep(wait_seconds)
    raise RuntimeError("Exceeded max retry attempts.")