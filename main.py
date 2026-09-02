# main.py — FastAPI entry point for AutoAnalyst
# Run with: uvicorn main:app --reload --port 8001

import shutil
import threading
import traceback
import uuid
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

sys.path.append("src/agent")
sys.path.append("src/auth")
sys.path.append("src/db")

from graph import build_graph_for_api
from routes import router as auth_router
from dependencies import get_current_user
from database import get_db, engine, Base
from models import User, Job

app = FastAPI(title="AutoAnalyst API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# make sure tables exist (safe to call every startup — does nothing if they already exist)
Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path(__file__).resolve().parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def run_pipeline(job_id: str, saved_path: Path, question: str, target_column: str | None):
    """Runs the full agent pipeline in a background thread, writing
    progress and results directly to PostgreSQL as it goes."""
    from database import SessionLocal
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = "running"
        db.commit()

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
            "target_col": target_column or "",
            "dataset_type": "",
            "id_cols": [],
            "needs_interpretability": True,
            "model_path": "", "model_name": "",
            "job_id": job_id,
            "messages": [],
        }

        final_state = app_graph.invoke(initial_state, config=config)

        job.status = "awaiting_approval"
        job.report = final_state.get("report", "")
        job.critique = final_state.get("critique", "")
        job.approved_by_critic = final_state.get("approved", False)
        job.revision_count = str(final_state.get("revision_count", 0))
        job.dataset_type = final_state.get("dataset_type", "")
        job.model_name = final_state.get("model_name", "")
        job.explanations = final_state.get("explanations", [])
        db.commit()

    except Exception as e:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = "failed"
        job.error = str(e)
        db.commit()
        print(f"ERROR in job {job_id}:")
        traceback.print_exc()

    finally:
        db.close()

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    question: str = "Analyze this dataset and summarize the key findings.",
    target_column: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Requires a valid auth token. The uploaded dataset and resulting
    job are tied to whichever user is currently logged in."""
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported.")

    job_id = str(uuid.uuid4())[:16]
    suffix = ".xlsx" if filename.endswith(".xlsx") else ".csv"
    saved_path = UPLOAD_DIR / f"{job_id}{suffix}"

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if suffix == ".xlsx":
        csv_path = UPLOAD_DIR / f"{job_id}.csv"
        pd.read_excel(saved_path).to_csv(csv_path, index=False)
        saved_path = csv_path

    # create the job record in PostgreSQL, owned by the current user
    job = Job(
        id=job_id,
        user_id=current_user.id,
        question=question,
        raw_path=str(saved_path),
        original_filename=file.filename,
        target_column=target_column,
        status="queued",
    )
    db.add(job)
    db.commit()

    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, saved_path, question, target_column),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def get_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns a job's status — only if it belongs to the current user."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # ownership check — this is the actual security enforcement
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this job.")

    response = {"job_id": job.id, "status": job.status}

    if job.status == "failed":
        response["error"] = job.error

    if job.status in ("awaiting_approval", "approved", "rejected"):
        response["result"] = {
            "report": job.report,
            "critique": job.critique,
            "approved_by_critic": job.approved_by_critic,
            "revision_count": job.revision_count,
            "target_col": job.target_column,
            "dataset_type": job.dataset_type,
            "model_name": job.model_name,
            "explanations": job.explanations,
            "human_decision": job.human_decision,
            "human_notes": job.human_notes,
        }

    return response


@app.get("/jobs")
def list_my_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists every job the current user has ever submitted —
    this is the 'retrieve previous analyses' requirement."""
    jobs = db.query(Job).filter(Job.user_id == current_user.id).order_by(Job.created_at.desc()).all()
    return [
        {"job_id": j.id, "question": j.question, "status": j.status, "created_at": j.created_at}
        for j in jobs
    ]


class ApprovalRequest(BaseModel):
    decision: str
    notes: str | None = None

@app.get("/charts/{job_id}/{filename}")
def get_chart(job_id: str, filename: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    chart_path = Path("data/plots") / filename
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Chart not found.")
    return FileResponse(chart_path)

@app.post("/approve/{job_id}")
def approve_report(
    job_id: str,
    body: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Human approval step — only the job's owner can approve/reject it."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this job.")

    if job.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail=f"Job is not awaiting approval (status: {job.status})")

    if body.decision not in ("approved", "rejected", "needs_revision"):
        raise HTTPException(status_code=400, detail="decision must be 'approved', 'rejected', or 'needs_revision'")

    job.status = body.decision
    job.human_decision = body.decision
    job.human_notes = body.notes or ""
    db.commit()

    return {"job_id": job_id, "status": job.status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)