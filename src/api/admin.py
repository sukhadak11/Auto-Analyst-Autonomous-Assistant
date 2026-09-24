from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import Job, User


router = APIRouter()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("/admin/dashboard")
def admin_dashboard(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return overall job statistics for admins.
    """

    # Only admins can access this endpoint
    if not current_user.is_admin:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    total_jobs = db.query(Job).count()

    completed_jobs = (
        db.query(Job)
        .filter(
            Job.status.in_(
                [
                    "awaiting_approval",
                    "approved",
                ]
            )
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

    running_jobs = (
        db.query(Job)
        .filter(
            Job.status == "running"
        )
        .count()
    )

    queued_jobs = (
        db.query(Job)
        .filter(
            Job.status == "queued"
        )
        .count()
    )

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "running_jobs": running_jobs,
        "queued_jobs": queued_jobs,
    }


# ============================================================
# ADMIN USERS
# ============================================================

@router.get("/admin/users")
def admin_users(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return all registered users.
    """

    if not current_user.is_admin:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    users = (
        db.query(User)
        .order_by(User.id)
        .all()
    )

    return [
        {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
        }
        for user in users
    ]


# ============================================================
# ADMIN JOBS
# ============================================================

@router.get("/admin/jobs")
def admin_jobs(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return all jobs for the admin dashboard.
    """

    if not current_user.is_admin:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    jobs = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .all()
    )

    return [
        {
            "job_id": job.id,
            "user_id": job.user_id,
            "question": job.question,
            "status": job.status,
            "original_filename": (
                job.original_filename
            ),
            "dataset_type": job.dataset_type,
            "model_name": job.model_name,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
        for job in jobs
    ]