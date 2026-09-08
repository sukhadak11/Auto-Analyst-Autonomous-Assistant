# src/db/models.py
# Defines the user and job database models. These are the tables that will be created in the database, and they define the structure of the data that will be stored.
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) # uuid.uuid4() generates a unique identifier.
    email = Column(String, unique=True, index=True, nullable=False) # nullable=False means that this column cannot be empty. Each user must have an email.
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    jobs = relationship("Job", back_populates="owner") # This sets up a relationship between the User and Job models. It allows you to access all jobs associated with a user via user.jobs, and it also allows you to access the owner of a job via job.owner. This is a one-to-many relationship


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)              # the job_id used everywhere
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # request details
    question = Column(Text, nullable=False)
    raw_path = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)
    target_column = Column(String, nullable=True)

    # lifecycle
    status = Column(String, default="queued") # job status          # queued, running, awaiting_approval, approved, rejected, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # intermediate + final results — stored as JSON so we don't need
    # a rigid column per possible field the pipeline might produce
    # They appear to store intermediate/final pipeline results.
    explanations = Column(JSON, nullable=True)
    generated_charts = Column(JSON, nullable=True)
    report = Column(Text, nullable=True)
    critique = Column(Text, nullable=True)
    approved_by_critic = Column(Boolean, nullable=True)
    revision_count = Column(String, nullable=True)
    dataset_type = Column(String, nullable=True)
    model_name = Column(String, nullable=True)

    # human decision
    human_decision = Column(String, nullable=True)
    human_notes = Column(Text, nullable=True)

    error = Column(Text, nullable=True) # If a job fails, the application can store the error information here.

    owner = relationship("User", back_populates="jobs") # This sets up the reverse relationship from Job to User. It allows you to access the owner of a job via job.owner, and it also allows you to access all jobs associated with a user via user.jobs. This is a many-to-one relationship.
    # This is important because SQLAlchemy uses back_populates to connect the two relationship properties.