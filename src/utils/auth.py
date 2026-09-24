# Now don't need to repeat authorization logic in every API.
from fastapi import HTTPException

from src.db.models import Job, User


def get_authorized_job(
    job_id: str,
    user: User,
    db
):
    """
    Get a job only if the current user
    is the owner or an admin.
    """

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if not user.is_admin and job.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    return job