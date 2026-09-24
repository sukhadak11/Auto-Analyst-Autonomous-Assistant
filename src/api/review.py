from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import Job, User

from src.api.pipeline_runner import run_pipeline
from src.utils.auth import get_authorized_job

from pathlib import Path
import threading


router = APIRouter()


# ============================================================
# REQUEST MODEL
# ============================================================

class ApprovalRequest(BaseModel):
    decision: str
    notes: str | None = None


# ============================================================
# APPROVE / REJECT / REQUEST REVISION
# ============================================================

@router.post("/approve/{job_id}")
def approve_job(
    job_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Handle human approval decisions for a completed job.

    Supported decisions:
        - approved
        - rejected
        - needs_revision
    """

    job = get_authorized_job(
        job_id,
        current_user,
        db,
    )

    decision = request.decision.lower().strip()

    valid_decisions = {
        "approved",
        "rejected",
        "needs_revision",
    }

    if decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid decision. Use "
                "'approved', 'rejected', "
                "or 'needs_revision'."
            ),
        )

    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------

    if decision == "approved":

        job.status = "approved"
        job.human_decision = "approved"
        job.human_notes = (
            request.notes or ""
        )

        db.commit()

        return {
            "job_id": job.id,
            "status": "approved",
            "message": (
                "Job approved successfully."
            ),
        }

    # --------------------------------------------------------
    # REJECTED
    # --------------------------------------------------------

    if decision == "rejected":

        job.status = "rejected"
        job.human_decision = "rejected"
        job.human_notes = (
            request.notes or ""
        )

        db.commit()

        return {
            "job_id": job.id,
            "status": "rejected",
            "message": (
                "Job rejected."
            ),
        }

    # --------------------------------------------------------
    # NEEDS REVISION
    # --------------------------------------------------------

    job.status = "needs_revision"
    job.human_decision = "needs_revision"
    job.human_notes = (
        request.notes or ""
    )

    db.commit()

    # --------------------------------------------------------
    # Re-run pipeline with feedback
    # --------------------------------------------------------

    if not job.raw_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Original dataset path "
                "not found."
            ),
        )

    saved_path = Path(job.raw_path)

    if not saved_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Original dataset file "
                "not found."
            ),
        )

    revision_question = job.question

    if job.human_notes:
        revision_question += (
            "\n\nHuman review feedback:\n"
            f"{job.human_notes}"
        )

    job.status = "queued"

    db.commit()

    thread = threading.Thread(
        target=run_pipeline,
        args=(
            job.id,
            saved_path,
            revision_question,
            job.target_column,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "job_id": job.id,
        "status": "queued",
        "message": (
            "Revision requested. "
            "The pipeline has been "
            "queued for reprocessing."
        ),
    }