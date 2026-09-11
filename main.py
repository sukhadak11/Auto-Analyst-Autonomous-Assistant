# main.py — FastAPI entry point for AutoAnalyst
# Run with:
# uvicorn main:app --reload --port 8001


import shutil
import threading
import traceback
import uuid
import sys
import joblib
import pandas as pd

from pathlib import Path
from typing import Dict, Any

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
)

from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from sqlalchemy.orm import Session


# ============================================================
# PATH CONFIGURATION
# ============================================================

sys.path.append("src/agent")
sys.path.append("src/auth")
sys.path.append("src/db")


# ============================================================
# PROJECT IMPORTS
# ============================================================

from graph import build_graph_for_api

from routes import router as auth_router

from dependencies import get_current_user

from database import (
    get_db,
    engine,
    Base,
)

from models import (
    User,
    Job,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AutoAnalyst API"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AUTH ROUTES
# ============================================================

app.include_router(
    auth_router
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

UPLOAD_DIR = (
    BASE_DIR
    / "data"
    / "uploads"
)

PLOTS_DIR = (
    BASE_DIR
    / "data"
    / "plots"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

PLOTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ApprovalRequest(BaseModel):
    decision: str
    notes: str | None = None


class PredictionRequest(BaseModel):
    features: Dict[str, Any]


# ============================================================
# CHART METADATA NORMALIZATION
# ============================================================

def normalize_generated_charts(
    charts,
):
    """
    Normalize chart metadata before storing it in PostgreSQL.

    Supported input formats:

    1. New format:
       {
           "chart_type": "...",
           "filename": "..."
       }

    2. Older tuple/list format:
       ("chart_type", "data/plots/chart.png")

    3. Plain path/string:
       "data/plots/chart.png"

    Final format:

    [
        {
            "chart_type": "...",
            "filename": "..."
        }
    ]
    """

    if not charts:
        return []

    normalized_charts = []

    for chart in charts:

        # ----------------------------------------------------
        # Dictionary format
        # ----------------------------------------------------

        if isinstance(
            chart,
            dict,
        ):

            filename = (
                chart.get("filename")
                or chart.get("file")
                or chart.get("name")
            )

            chart_type = (
                chart.get("chart_type")
                or "visualization"
            )

            if filename:

                filename = Path(
                    str(filename)
                ).name

                normalized_charts.append(
                    {
                        "chart_type": str(
                            chart_type
                        ),
                        "filename": filename,
                    }
                )

        # ----------------------------------------------------
        # Tuple / list format
        # ----------------------------------------------------

        elif isinstance(
            chart,
            (tuple, list),
        ):

            if len(chart) >= 2:

                chart_type = chart[0]

                chart_path = chart[1]

                filename = Path(
                    str(chart_path)
                ).name

                normalized_charts.append(
                    {
                        "chart_type": str(
                            chart_type
                        ),
                        "filename": filename,
                    }
                )

        # ----------------------------------------------------
        # String/path format
        # ----------------------------------------------------

        elif chart:

            filename = Path(
                str(chart)
            ).name

            normalized_charts.append(
                {
                    "chart_type": "visualization",
                    "filename": filename,
                }
            )

    # --------------------------------------------------------
    # Remove duplicate filenames
    # --------------------------------------------------------

    unique_charts = []

    seen_files = set()

    for chart in normalized_charts:

        filename = chart.get(
            "filename"
        )

        if (
            filename
            and filename not in seen_files
        ):

            unique_charts.append(
                chart
            )

            seen_files.add(
                filename
            )

    return unique_charts


# ============================================================
# RUN ANALYSIS PIPELINE
# ============================================================

def run_pipeline(
    job_id: str,
    saved_path: Path,
    question: str,
    target_column: str | None,
):
    """
    Runs the full LangGraph analysis pipeline in a background
    thread and stores the final results in PostgreSQL.
    """

    from database import SessionLocal

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Get job
        # ----------------------------------------------------

        job = (
            db.query(Job)
            .filter(
                Job.id == job_id
            )
            .first()
        )

        if not job:

            print(
                f"Job {job_id} not found."
            )

            return

        # ----------------------------------------------------
        # Mark job as running
        # ----------------------------------------------------

        job.status = "running"

        # Clear previous error/review state.
        job.error = None
        job.human_decision = None
        job.human_notes = None

        db.commit()

        # ----------------------------------------------------
        # Build LangGraph
        # ----------------------------------------------------

        app_graph = (
            build_graph_for_api()
        )

        config = {
            "configurable": {
                "thread_id": job_id
            }
        }

        # ----------------------------------------------------
        # Initial agent state
        # ----------------------------------------------------

        initial_state = {

            "question": question,

            "plan": [],

            "required_agents": [],

            "data_findings": "",

            "research_findings": "",

            "report": "",

            "critique": "",

            "approved": False,

            "revision_count": 0,

            "human_decision": "",

            "human_notes": "",

            "explanations": [],

            "generated_charts": [],

            "raw_path": str(
                saved_path
            ),

            "clean_path": "",

            "target_col": (
                target_column
                or ""
            ),

            "dataset_type": "",

            "id_cols": [],

            "needs_interpretability": True,

            "model_path": "",

            "model_name": "",

            "feature_importance": [],

            "job_id": job_id,

            "messages": [],
        }

        # ----------------------------------------------------
        # Run graph
        # ----------------------------------------------------

        final_state = app_graph.invoke(
            initial_state,
            config=config,
        )

        # ----------------------------------------------------
        # Save analysis results
        # ----------------------------------------------------

        job.status = (
            "awaiting_approval"
        )

        job.report = (
            final_state.get(
                "report",
                "",
            )
        )

        job.critique = (
            final_state.get(
                "critique",
                "",
            )
        )

        job.approved_by_critic = (
            final_state.get(
                "approved",
                False,
            )
        )

        job.revision_count = str(
            final_state.get(
                "revision_count",
                0,
            )
        )

        job.dataset_type = (
            final_state.get(
                "dataset_type",
                "",
            )
        )

        job.model_name = (
            final_state.get(
                "model_name",
                "",
            )
        )

        job.explanations = (
            final_state.get(
                "explanations",
                [],
            )
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Normalize generated chart metadata before saving.
        # ----------------------------------------------------

        raw_charts = (
            final_state.get(
                "generated_charts",
                [],
            )
        )

        job.generated_charts = (
            normalize_generated_charts(
                raw_charts
            )
        )

        # ----------------------------------------------------
        # Fresh human review
        # ----------------------------------------------------

        job.human_decision = None

        job.human_notes = None

        # ----------------------------------------------------
        # Save everything
        # ----------------------------------------------------

        db.commit()

        print(
            f"Job {job_id} completed "
            "and is awaiting human approval."
        )

    except Exception as e:

        # ----------------------------------------------------
        # Mark job as failed
        # ----------------------------------------------------

        job = (
            db.query(Job)
            .filter(
                Job.id == job_id
            )
            .first()
        )

        if job:

            job.status = "failed"

            job.error = str(e)

            db.commit()

        print(
            f"ERROR in job {job_id}:"
        )

        traceback.print_exc()

    finally:

        db.close()


# ============================================================
# UPLOAD DATASET
# ============================================================

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),

    question: str = (
        "Analyze this dataset and "
        "summarize the key findings."
    ),

    target_column: str | None = None,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Upload a CSV/XLSX dataset and
    start an analysis job.
    """

    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = (
        file.filename.lower()
    )

    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    if not (
        filename.endswith(".csv")
        or filename.endswith(".xlsx")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV and XLSX "
                "files are supported."
            ),
        )

    # --------------------------------------------------------
    # Generate job ID
    # --------------------------------------------------------

    job_id = str(
        uuid.uuid4()
    )[:16]

    suffix = (
        ".xlsx"
        if filename.endswith(".xlsx")
        else ".csv"
    )

    saved_path = (
        UPLOAD_DIR
        / f"{job_id}{suffix}"
    )

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    with open(
        saved_path,
        "wb",
    ) as f:

        shutil.copyfileobj(
            file.file,
            f,
        )

    # --------------------------------------------------------
    # Convert XLSX to CSV
    # --------------------------------------------------------

    if suffix == ".xlsx":

        csv_path = (
            UPLOAD_DIR
            / f"{job_id}.csv"
        )

        pd.read_excel(
            saved_path
        ).to_csv(
            csv_path,
            index=False,
        )

        saved_path = csv_path

    # --------------------------------------------------------
    # Create database job
    # --------------------------------------------------------

    job = Job(

        id=job_id,

        user_id=current_user.id,

        question=question,

        raw_path=str(
            saved_path
        ),

        original_filename=(
            file.filename
        ),

        target_column=target_column,

        status="queued",
    )

    db.add(job)

    db.commit()

    # --------------------------------------------------------
    # Start background pipeline
    # --------------------------------------------------------

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
    }


# ============================================================
# GET JOB STATUS
# ============================================================

@app.get("/status/{job_id}")
def get_status(
    job_id: str,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Returns job status and analysis results.

    Admin:
        Can view any job.

    Normal user:
        Can view only their own job.
    """

    # --------------------------------------------------------
    # Find job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # --------------------------------------------------------
    # Access control
    # --------------------------------------------------------

    if (
        not current_user.is_admin
        and job.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have "
                "access to this job."
            ),
        )

    response = {
        "job_id": job.id,
        "status": job.status,
    }

    # --------------------------------------------------------
    # Failed job
    # --------------------------------------------------------

    if job.status == "failed":

        response["error"] = (
            job.error
        )

    # --------------------------------------------------------
    # Completed / review results
    # --------------------------------------------------------

    if job.status in (
        "awaiting_approval",
        "approved",
        "rejected",
    ):

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

            # IMPORTANT:
            # Frontend reads this field.
            "generated_charts": (
                job.generated_charts
                or []
            ),

            "human_decision": (
                job.human_decision
            ),

            "human_notes": (
                job.human_notes
            ),
        }

    return response


# ============================================================
# PREDICTION
# ============================================================

@app.post("/predict/{job_id}")
def predict_for_instance(
    job_id: str,

    body: PredictionRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Generate a prediction using
    the trained model for a job.
    """

    # --------------------------------------------------------
    # Find job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # --------------------------------------------------------
    # Access control
    # --------------------------------------------------------

    if (
        not current_user.is_admin
        and job.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    # --------------------------------------------------------
    # Check job status
    # --------------------------------------------------------

    if job.status not in (
        "awaiting_approval",
        "approved",
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Model not yet trained "
                "for this job."
            ),
        )

    # --------------------------------------------------------
    # Model path
    # --------------------------------------------------------

    model_path = (
        BASE_DIR
        / "data"
        / f"model_{job_id}.joblib"
    )

    if not model_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Trained model file "
                "not found."
            ),
        )

    try:

        model = joblib.load(
            model_path
        )

        # ----------------------------------------------------
        # Build input dataframe
        # ----------------------------------------------------

        input_df = pd.DataFrame(
            [body.features]
        )

        # ----------------------------------------------------
        # Validate expected columns
        # ----------------------------------------------------

        if not hasattr(
            model,
            "feature_names_in_",
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "The trained model "
                    "does not expose "
                    "feature names."
                ),
            )

        expected_cols = (
            model.feature_names_in_
        )

        missing = [
            column
            for column in expected_cols
            if column
            not in input_df.columns
        ]

        if missing:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Missing required "
                    f"feature(s): {missing}. "
                    f"Model expects: "
                    f"{list(expected_cols)}"
                ),
            )

        # ----------------------------------------------------
        # Correct column order
        # ----------------------------------------------------

        input_df = input_df[
            expected_cols
        ]

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        prediction = int(
            model.predict(
                input_df
            )[0]
        )

        result = {
            "job_id": job_id,
            "prediction": prediction,
        }

        # ----------------------------------------------------
        # Probability
        # ----------------------------------------------------

        if hasattr(
            model,
            "predict_proba",
        ):

            probabilities = (
                model.predict_proba(
                    input_df
                )[0]
            )

            # Binary classification
            if len(
                probabilities
            ) == 2:

                result[
                    "churn_probability"
                ] = round(
                    float(
                        probabilities[1]
                    ),
                    4,
                )

            # Multi-class classification
            else:

                result[
                    "probabilities"
                ] = [
                    round(
                        float(p),
                        4,
                    )
                    for p in probabilities
                ]

        return result

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Prediction failed: {str(e)}"
            ),
        )


# ============================================================
# LIST JOBS
# ============================================================

@app.get("/jobs")
def list_jobs(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Admin:
        Can see all users' jobs.

    Normal user:
        Can see only their own jobs.
    """

    if current_user.is_admin:

        jobs = (
            db.query(Job)
            .order_by(
                Job.created_at.desc()
            )
            .all()
        )

    else:

        jobs = (
            db.query(Job)
            .filter(
                Job.user_id
                == current_user.id
            )
            .order_by(
                Job.created_at.desc()
            )
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

@app.get("/reports")
def list_reports(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Returns completed analysis reports.

    Admin:
        Can see reports from all users.

    Normal user:
        Can see only their own reports.
    """

    if current_user.is_admin:

        jobs = (
            db.query(Job)
            .filter(
                Job.report.isnot(None),
                Job.report != "",
            )
            .order_by(
                Job.created_at.desc()
            )
            .all()
        )

    else:

        jobs = (
            db.query(Job)
            .filter(
                Job.user_id
                == current_user.id,

                Job.report.isnot(None),

                Job.report != "",
            )
            .order_by(
                Job.created_at.desc()
            )
            .all()
        )

    return [

        {
            "job_id": job.id,

            "user_id": job.user_id,

            "question": job.question,

            "status": job.status,

            "report": job.report,

            "dataset_type": (
                job.dataset_type
            ),

            "model_name": (
                job.model_name
            ),

            "created_at": (
                job.created_at
            ),

            "updated_at": (
                job.updated_at
            ),
        }

        for job in jobs
    ]


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.get("/admin/dashboard")
def admin_dashboard(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Returns dashboard statistics
    for administrators.
    """

    # --------------------------------------------------------
    # Admin access check
    # --------------------------------------------------------

    if not current_user.is_admin:

        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    # --------------------------------------------------------
    # User statistics
    # --------------------------------------------------------

    total_users = (
        db.query(User).count()
    )

    active_users = (
        db.query(User)
        .filter(
            User.is_active == True
        )
        .count()
    )

    admin_users = (
        db.query(User)
        .filter(
            User.is_admin == True
        )
        .count()
    )

    normal_users = (
        db.query(User)
        .filter(
            User.is_admin == False
        )
        .count()
    )

    # --------------------------------------------------------
    # Job statistics
    # --------------------------------------------------------

    total_jobs = (
        db.query(Job).count()
    )

    queued_jobs = (
        db.query(Job)
        .filter(
            Job.status == "queued"
        )
        .count()
    )

    running_jobs = (
        db.query(Job)
        .filter(
            Job.status == "running"
        )
        .count()
    )

    awaiting_approval_jobs = (
        db.query(Job)
        .filter(
            Job.status
            == "awaiting_approval"
        )
        .count()
    )

    approved_jobs = (
        db.query(Job)
        .filter(
            Job.status == "approved"
        )
        .count()
    )

    rejected_jobs = (
        db.query(Job)
        .filter(
            Job.status == "rejected"
        )
        .count()
    )

    needs_revision_jobs = (
        db.query(Job)
        .filter(
            Job.status
            == "needs_revision"
        )
        .count()
    )

    failed_jobs = (
        db.query(Job)
        .filter(
            Job.status == "failed"
        )
        .count()
    )

    return {

        "users": {

            "total": total_users,

            "active": active_users,

            "admins": admin_users,

            "normal_users": normal_users,
        },

        "jobs": {

            "total": total_jobs,

            "queued": queued_jobs,

            "running": running_jobs,

            "awaiting_approval": (
                awaiting_approval_jobs
            ),

            "approved": approved_jobs,

            "rejected": rejected_jobs,

            "needs_revision": (
                needs_revision_jobs
            ),

            "failed": failed_jobs,
        },
    }


# ============================================================
# ADMIN USERS
# ============================================================

@app.get("/admin/users")
def admin_users(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Returns all users for the
    Admin Dashboard.
    """

    if not current_user.is_admin:

        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    users = (
        db.query(User)
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    result = []

    for user in users:

        user_job_count = (
            db.query(Job)
            .filter(
                Job.user_id
                == user.id
            )
            .count()
        )

        result.append(
            {
                "user_id": user.id,

                "email": user.email,

                "is_admin": user.is_admin,

                "is_active": (
                    user.is_active
                ),

                "created_at": (
                    user.created_at
                ),

                "job_count": (
                    user_job_count
                ),
            }
        )

    return result


# ============================================================
# ADMIN JOBS
# ============================================================

@app.get("/admin/jobs")
def admin_jobs(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Returns all jobs for the
    Admin Dashboard.
    """

    if not current_user.is_admin:

        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    jobs = (
        db.query(Job)
        .order_by(
            Job.created_at.desc()
        )
        .all()
    )

    return [

        {
            "job_id": job.id,

            "user_id": job.user_id,

            "question": job.question,

            "status": job.status,

            "dataset_type": (
                job.dataset_type
            ),

            "model_name": (
                job.model_name
            ),

            "created_at": (
                job.created_at
            ),

            "updated_at": (
                job.updated_at
            ),
        }

        for job in jobs
    ]


# ============================================================
# GET GENERATED CHART
# ============================================================

@app.get(
    "/charts/{job_id}/{filename}"
)
def get_chart(
    job_id: str,

    filename: str,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Returns a generated PNG visualization.

    Admin:
        Can access charts from any job.

    Normal user:
        Can access charts from their own jobs.
    """

    # --------------------------------------------------------
    # Find job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # --------------------------------------------------------
    # Access control
    # --------------------------------------------------------

    if (
        not current_user.is_admin
        and job.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    # --------------------------------------------------------
    # Prevent path traversal
    # --------------------------------------------------------

    safe_filename = Path(
        filename
    ).name

    if safe_filename != filename:

        raise HTTPException(
            status_code=400,
            detail="Invalid chart filename.",
        )

    # --------------------------------------------------------
    # Chart path
    # --------------------------------------------------------

    chart_path = (
        PLOTS_DIR
        / safe_filename
    )

    # --------------------------------------------------------
    # Check file exists
    # --------------------------------------------------------

    if not chart_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Chart not found: "
                f"{safe_filename}"
            ),
        )

    # --------------------------------------------------------
    # Return PNG
    # --------------------------------------------------------

    return FileResponse(
        chart_path,
        media_type="image/png",
    )


# ============================================================
# HUMAN APPROVAL
# ============================================================

@app.post("/approve/{job_id}")
def approve_job(
    job_id: str,

    body: ApprovalRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):
    """
    Human approval step.

    Admin:
        Can approve/reject/request revision
        for any user's job.

    Normal user:
        Can approve/reject/request revision
        only for their own job.
    """

    # --------------------------------------------------------
    # Find job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # --------------------------------------------------------
    # Access control
    # --------------------------------------------------------

    if (
        not current_user.is_admin
        and job.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have "
                "access to this job."
            ),
        )

    # --------------------------------------------------------
    # Check status
    # --------------------------------------------------------

    if job.status != (
        "awaiting_approval"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Job cannot be reviewed "
                f"while in '{job.status}' "
                "status."
            ),
        )

    # --------------------------------------------------------
    # Validate decision
    # --------------------------------------------------------

    if body.decision not in {
        "approved",
        "rejected",
        "needs_revision",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Decision must be "
                "'approved', 'rejected', "
                "or 'needs_revision'."
            ),
        )

    # --------------------------------------------------------
    # Save human review
    # --------------------------------------------------------

    job.human_decision = (
        body.decision
    )

    job.human_notes = (
        body.notes or ""
    )

    # ========================================================
    # APPROVED
    # ========================================================

    if body.decision == "approved":

        job.status = "approved"

        db.commit()

        db.refresh(job)

        return {

            "job_id": job.id,

            "status": job.status,

            "human_decision": (
                job.human_decision
            ),

            "human_notes": (
                job.human_notes
            ),

            "message": (
                "Analysis approved "
                "successfully."
            ),
        }

    # ========================================================
    # REJECTED
    # ========================================================

    if body.decision == "rejected":

        job.status = "rejected"

        db.commit()

        db.refresh(job)

        return {

            "job_id": job.id,

            "status": job.status,

            "human_decision": (
                job.human_decision
            ),

            "human_notes": (
                job.human_notes
            ),

            "message": (
                "Analysis rejected."
            ),
        }

    # ========================================================
    # NEEDS REVISION
    # ========================================================

    job.status = "queued"

    db.commit()

    db.refresh(job)

    # --------------------------------------------------------
    # Preserve original question + feedback
    # --------------------------------------------------------

    revision_question = (

        f"{job.question}\n\n"

        "Human review feedback:\n"

        f"{body.notes.strip() if body.notes else 'Please review and improve the analysis.'}"
    )

    # --------------------------------------------------------
    # Verify dataset exists
    # --------------------------------------------------------

    raw_path = Path(
        job.raw_path
    )

    if not raw_path.exists():

        job.status = "failed"

        job.error = (
            "Original dataset file not found. "
            "Revision cannot be started."
        )

        db.commit()

        raise HTTPException(
            status_code=404,
            detail=(
                "Original dataset file "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # Restart pipeline
    # --------------------------------------------------------

    thread = threading.Thread(

        target=run_pipeline,

        args=(

            job.id,

            raw_path,

            revision_question,

            job.target_column,
        ),

        daemon=True,
    )

    thread.start()

    return {

        "job_id": job.id,

        "status": "queued",

        "human_decision": (
            "needs_revision"
        ),

        "human_notes": (
            body.notes or ""
        ),

        "message": (
            "Revision requested. "
            "The analysis pipeline "
            "has been restarted."
        ),
    }


# ============================================================
# REPROCESS JOB
# ============================================================

@app.post(
    "/reprocess/{job_id}"
)
def reprocess_job(
    job_id: str,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Reprocess a job that is waiting
    for revision.
    """

    # --------------------------------------------------------
    # Find job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # --------------------------------------------------------
    # Access control
    # --------------------------------------------------------

    if (
        not current_user.is_admin
        and job.user_id
        != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    # --------------------------------------------------------
    # Check status
    # --------------------------------------------------------

    if job.status != (
        "needs_revision"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Job cannot be reprocessed "
                f"while in '{job.status}' "
                "status."
            ),
        )

    # --------------------------------------------------------
    # Check original dataset
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Build revised question
    # --------------------------------------------------------

    revision_question = (
        job.question
    )

    if job.human_notes:

        revision_question = (

            f"{job.question}\n\n"

            "Human review feedback:\n"

            f"{job.human_notes}"
        )

    # --------------------------------------------------------
    # Queue job
    # --------------------------------------------------------

    job.status = "queued"

    job.error = None

    db.commit()

    # --------------------------------------------------------
    # Start pipeline
    # --------------------------------------------------------

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


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )