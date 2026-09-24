from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import User

from src.utils.auth import get_authorized_job
from src.utils.paths import (
    PLOTS_DIR,
    get_job_csv_path,
    get_job_model_path,
)


router = APIRouter()


# ============================================================
# GENERATED CHART
# ============================================================

@router.get("/charts/{job_id}/{filename}")
def get_chart(
    job_id: str,
    filename: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return a generated chart for an authorized job.
    """

    # Verify job access
    get_authorized_job(
        job_id,
        current_user,
        db,
    )

    # Prevent path traversal
    safe_filename = Path(filename).name

    chart_path = PLOTS_DIR / safe_filename

    if not chart_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Chart not found.",
        )

    return FileResponse(
        path=str(chart_path),
        media_type="image/png",
        filename=safe_filename,
    )


# ============================================================
# ORIGINAL DATASET
# ============================================================

@router.get("/download/{job_id}/csv")
def download_csv(
    job_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Download the original dataset associated
    with an authorized job.
    """

    job = get_authorized_job(
        job_id,
        current_user,
        db,
    )

    csv_path = get_job_csv_path(job_id)

    if not csv_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found.",
        )

    filename = (
        job.original_filename
        or "dataset.csv"
    )

    # Ensure downloaded file remains CSV
    if not filename.lower().endswith(".csv"):
        filename = Path(filename).stem + ".csv"

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=filename,
    )


# ============================================================
# TRAINED MODEL
# ============================================================

@router.get("/download/{job_id}/model")
def download_model(
    job_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Download the trained model associated
    with an authorized job.
    """

    get_authorized_job(
        job_id,
        current_user,
        db,
    )

    model_path = get_job_model_path(job_id)

    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Trained model not found.",
        )

    return FileResponse(
        path=str(model_path),
        media_type="application/octet-stream",
        filename="trained_model.joblib",
    )