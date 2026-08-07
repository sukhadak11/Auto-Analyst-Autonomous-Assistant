# src/api/main.py — add these imports
import os
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException

# create FastAPI app and upload directory
app = FastAPI()
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ensure the project's src/agent directory is on the import path
# file is at src/api/main.py, so go up one level to src and then into agent
sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))
from graph import build_graph

# simple in-memory job store (fine for a single-user local app)
jobs = {}

def run_pipeline(job_id: str, csv_path: Path, question: str, target_column: str):
    jobs[job_id]["status"] = "running"
    try:
        fixed_raw_path = Path("data/raw_data.csv")
        shutil.copyfile(csv_path, fixed_raw_path)
        print(f"DEBUG: copied {csv_path} -> {fixed_raw_path}, size: {fixed_raw_path.stat().st_size} bytes")

        os.environ["AUTOANALYST_TARGET_COL"] = target_column   # <-- pass via env var, simplest path

        app_graph = build_graph()
        jobs[job_id]["status"] = "completed"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"ERROR in job {job_id}: {e}")

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    question: str = "Analyze this dataset and summarize the key findings.",
    target_column: str = None,
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    job_id = str(uuid.uuid4())[:8]
    saved_path = UPLOAD_DIR / f"{job_id}.csv"

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    print(f"DEBUG: saved upload to {saved_path.resolve()}, size={saved_path.stat().st_size}")

    # if target_column not given, try to guess it (last column is a common default)
    if not target_column:
        import pandas as pd
        preview = pd.read_csv(saved_path, nrows=5)
        target_column = preview.columns[-1]
        print(f"DEBUG: no target_column given, guessed: {target_column}")

    jobs[job_id] = {"status": "queued", "created_at": datetime.now().isoformat()}
    thread = threading.Thread(target=run_pipeline, args=(job_id, saved_path, question, target_column))
    thread.start()

    return {"job_id": job_id, "status": "queued", "target_column": target_column}