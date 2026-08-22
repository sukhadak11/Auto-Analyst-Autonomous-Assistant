# src/db/models.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    jobs = relationship("Job", back_populates="owner")


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
    status = Column(String, default="queued")           # queued, running, awaiting_approval, approved, rejected, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # intermediate + final results — stored as JSON so we don't need
    # a rigid column per possible field the pipeline might produce
    explanations = Column(JSON, nullable=True)
    report = Column(Text, nullable=True)
    critique = Column(Text, nullable=True)
    approved_by_critic = Column(Boolean, nullable=True)
    revision_count = Column(String, nullable=True)
    dataset_type = Column(String, nullable=True)
    model_name = Column(String, nullable=True)

    # human decision
    human_decision = Column(String, nullable=True)
    human_notes = Column(Text, nullable=True)

    # error info, if the job failed
    error = Column(Text, nullable=True)

    owner = relationship("User", back_populates="jobs")