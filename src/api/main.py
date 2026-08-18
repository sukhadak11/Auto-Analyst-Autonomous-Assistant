import os
import shutil
import sys
import threading
import traceback
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AutoAnalyst API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))
from graph import build_graph_for_api  # see note below — new function, not build_graph()

# in-memory job store (fine for a single-user local app; swap for Redis/DB for multi-user)
jobs = {}


def run_pipeline(job_id: str, saved_path: Path, question: str, target_column: str | None):
    jobs[job_id]["status"] = "running"
    try:
        app_graph = build_graph_for_api()
        config = {"configurable": {"thread_id": job_id}}

        initial_state = {
            "question": question,
            "plan": [], "data_findings": "", "research_findings": "", "report": "",
            "critique": "", "approved": False, "revision_count": 0,
            "human_decision": "", "human_notes": "",
            "explanations": [],
            "raw_path": str(saved_path),
            "clean_path": "",
            "target_col": target_column or "",   # empty string -> Profiling Agent auto-detects
            "dataset_type": "",
            "id_cols": [],
            "needs_interpretability": True,
            "model_path": "", "model_name": "",
            "job_id": job_id,
            "messages": [],
        }

        final_state = app_graph.invoke(initial_state, config=config)

        jobs[job_id]["status"] = "awaiting_approval"
        jobs[job_id]["result"] = {
            "report": final_state.get("report", ""),
            "critique": final_state.get("critique", ""),
            "approved_by_critic": final_state.get("approved", False),
            "revision_count": final_state.get("revision_count", 0),
            "target_col": final_state.get("target_col", ""),
            "dataset_type": final_state.get("dataset_type", ""),
            "model_name": final_state.get("model_name", ""),
            "explanations": final_state.get("explanations", []),
        }
        jobs[job_id]["final_state"] = final_state  # kept in memory so /approve can resume if needed

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"ERROR in job {job_id}: {e}")
        traceback.print_exc()  # for debugging; in production, consider logging to a file instead


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    question: str = "Analyze this dataset and summarize the key findings.",
    target_column: str | None = None,
):
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV or Excel (.xlsx) files are supported.")

    job_id = str(uuid.uuid4())[:16]  # short UUID for easier reference
    suffix = ".xlsx" if file.filename.endswith(".xlsx") else ".csv"
    saved_path = UPLOAD_DIR / f"{job_id}{suffix}"

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
# instead of using shutil.copyfileobj, you could also use file.file.read() and f.write(), but copyfileobj is more efficient for large files.
    # Excel gets converted to CSV once here, so every downstream agent
    # only ever has to deal with one file format
    if suffix == ".xlsx":
        csv_path = UPLOAD_DIR / f"{job_id}.csv"
        pd.read_excel(saved_path).to_csv(csv_path, index=False)
        saved_path = csv_path

    print(f"DEBUG: saved upload to {saved_path.resolve()}, size={saved_path.stat().st_size}")

    jobs[job_id] = {"status": "queued", "created_at": datetime.now().isoformat()}
    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, saved_path, question, target_column),
    )
    thread.start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    response = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "failed":
        response["error"] = job.get("error")
    if job["status"] in ("awaiting_approval", "approved", "rejected"):
        response["result"] = job.get("result")
    return response


class ApprovalRequest(BaseModel):
    decision: str          # "approved" | "rejected" | "needs_revision"
    notes: str | None = None


@app.post("/approve/{job_id}")
def approve_report(job_id: str, body: ApprovalRequest):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "awaiting_approval":
        raise HTTPException(status_code=400, detail=f"Job is not awaiting approval (status: {job['status']}).")

    if body.decision not in ("approved", "rejected", "needs_revision"):
        raise HTTPException(status_code=400, detail="decision must be 'approved', 'rejected', or 'needs_revision'.")

    job["status"] = body.decision
    job["result"]["human_decision"] = body.decision
    job["result"]["human_notes"] = body.notes or ""

    return {"job_id": job_id, "status": job["status"]}