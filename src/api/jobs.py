import shutil
import threading
import uuid
from pathlib import Path

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import Job, User

from src.api.pipeline_runner import run_pipeline

from src.utils.auth import get_authorized_job
from src.utils.data import get_dataset_preview
from src.utils.paths import (
    BASE_DIR,
    PLOTS_DIR,
    get_job_csv_path,
    get_job_model_path,
    get_job_output_dir,
    ensure_job_output_dirs,
)

router = APIRouter()


# ============================================================
# UPLOAD
# ============================================================

@router.post("/upload")
async def upload_dataset(
    question: str = Form(...),
    file: UploadFile = File(...),
    target_column: str | None = None,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    filename = file.filename.lower()

    if not filename.endswith(
        (".csv", ".xlsx")
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV and XLSX "
                "files are supported."
            )
        )

    job_id = str(uuid.uuid4())[:16]

    ensure_job_output_dirs(job_id)

    saved_path = get_job_csv_path(job_id)

    # Convert XLSX to CSV
    if filename.endswith(".xlsx"):

        pd.read_excel(
            file.file
        ).to_csv(
            saved_path,
            index=False
        )

    # Save CSV directly
    else:

        with open(
            saved_path,
            "wb"
        ) as output:

            shutil.copyfileobj(
                file.file,
                output
            )

    # Create database record
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

    # Start background pipeline
    thread = threading.Thread(
        target=run_pipeline,
        args=(
            job_id,
            saved_path,
            question,
            target_column,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "job_id": job_id,
        "status": "queued",
        "output_directory": str(
            get_job_output_dir(job_id)
            .relative_to(BASE_DIR)
        ),
    }


# ============================================================
# STATUS
# ============================================================

@router.get("/status/{job_id}")
def get_status(
    job_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    job = get_authorized_job(
        job_id,
        current_user,
        db
    )

    response = {
        "job_id": job.id,
        "status": job.status,
    }

    if job.status == "failed":

        response["error"] = job.error

    if job.status in {
        "awaiting_approval",
        "approved",
        "rejected",
    }:

        response["result"] = {
            "report": job.report,
            "critique": job.critique,
            "approved_by_critic": (
                job.approved_by_critic
            ),
            "revision_count": (
                job.revision_count
            ),
            "target_col": (
                job.target_column
            ),
            "dataset_type": (
                job.dataset_type
            ),
            "model_name": (
                job.model_name
            ),
            "explanations": (
                job.explanations
            ),
            "generated_charts": (
                job.generated_charts or []
            ),
            "human_decision": (
                job.human_decision
            ),
            "human_notes": (
                job.human_notes
            ),
            "question": job.question,
            "dataset": get_dataset_preview(
                Path(job.raw_path)
            ),
        }

    return response


# ============================================================
# ALL JOBS
# ============================================================

@router.get("/jobs")
def list_jobs(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    query = db.query(Job)

    if not current_user.is_admin:

        query = query.filter(
            Job.user_id == current_user.id
        )

    jobs = (
        query
        .order_by(Job.created_at.desc())
        .all()
    )

    return [
        {
            "job_id": job.id,
            "user_id": job.user_id,
            "question": job.question,
            "status": job.status,
            "created_at": job.created_at,
        }
        for job in jobs
    ]


# ============================================================
# REPORTS
# ============================================================

@router.get("/reports")
def list_reports(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    query = (
        db.query(Job)
        .filter(
            Job.report.isnot(None),
            Job.report != ""
        )
    )

    if not current_user.is_admin:

        query = query.filter(
            Job.user_id == current_user.id
        )

    jobs = (
        query
        .order_by(Job.created_at.desc())
        .all()
    )

    return [
        {
            "job_id": job.id,
            "user_id": job.user_id,
            "question": job.question,
            "status": job.status,
            "report": job.report,
            "dataset_type": job.dataset_type,
            "model_name": job.model_name,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
        for job in jobs
    ]


# ============================================================
# DELETE JOB
# ============================================================

@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    job = get_authorized_job(
        job_id,
        current_user,
        db
    )

    # Delete dataset
    if job.raw_path:

        raw_path = Path(
            job.raw_path
        )

        if raw_path.exists():

            try:
                raw_path.unlink()
            except OSError:
                pass

    # Delete charts
    for chart in (
        job.generated_charts or []
    ):

        if not isinstance(
            chart,
            dict
        ):
            continue

        filename = chart.get(
            "filename"
        )

        if not filename:
            continue

        chart_path = (
            PLOTS_DIR
            / Path(filename).name
        )

        if chart_path.exists():

            try:
                chart_path.unlink()
            except OSError:
                pass

    # Delete model
    model_path = get_job_model_path(
        job_id
    )

    if model_path.exists():

        try:
            model_path.unlink()
        except OSError:
            pass

    # Delete complete job folder
    output_dir = get_job_output_dir(
        job_id
    )

    if output_dir.exists():

        try:
            shutil.rmtree(
                output_dir
            )
        except OSError:
            pass

    # Legacy model
    legacy_model = (
        BASE_DIR
        / "data"
        / f"model_{job_id}.joblib"
    )

    if legacy_model.exists():

        try:
            legacy_model.unlink()
        except OSError:
            pass

    # Delete database record
    db.delete(job)
    db.commit()

    return {
        "job_id": job_id,
        "message": (
            "Job deleted successfully."
        ),
    }


# ============================================================
# REPROCESS
# ============================================================

@router.post("/reprocess/{job_id}")
def reprocess_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    job = get_authorized_job(
        job_id,
        current_user,
        db
    )

    if job.status != "needs_revision":

        raise HTTPException(
            status_code=400,
            detail=(
                "Job cannot be reprocessed "
                f"while in '{job.status}' "
                "status."
            ),
        )

    saved_path = Path(
        job.raw_path
    )

    if not saved_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Original uploaded dataset "
                "could not be found."
            ),
        )

    revision_question = job.question

    if job.human_notes:

        revision_question += (
            "\n\nHuman review feedback:\n"
            f"{job.human_notes}"
        )

    job.status = "queued"
    job.error = None

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
            "Job revision has been "
            "queued for reprocessing."
        ),
    }