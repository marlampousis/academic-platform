
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    # Match the existing application's naive UTC timestamps.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AIRun(Base):
    __tablename__ = "ai_runs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')",
            name="ck_ai_run_status",
        ),
    )

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    task_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    latency_ms = Column(Integer, nullable=True)
    error_code = Column(String(100), nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")

    artifacts = relationship(
        "AIArtifact",
        back_populates="run",
    )


class AIArtifact(Base):
    __tablename__ = "ai_artifacts"

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'REVIEW_REQUIRED', 'IN_REVIEW', "
            "'APPROVED', 'REJECTED')",
            name="ck_ai_artifact_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_ai_artifact_version",
        ),
        Index(
            "ix_ai_artifacts_owner_type",
            "owner_user_id",
            "artifact_type",
        ),
    )

    id = Column(Integer, primary_key=True)

    run_id = Column(
        Integer,
        ForeignKey("ai_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    owner_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    application_id = Column(
        Integer,
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    committee_assignment_id = Column(
        Integer,
        ForeignKey("committee_applications.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    artifact_type = Column(String(50), nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="REVIEW_REQUIRED",
    )

    payload_json = Column(JSONB, nullable=False)

    version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    run = relationship(
        "AIRun",
        back_populates="artifacts",
    )

    owner = relationship("User")
    application = relationship("Application")
    committee_assignment = relationship("CommitteeApplication")

    evidence = relationship(
        "AIEvidence",
        back_populates="artifact",
    )

    review_events = relationship(
        "AIReviewEvent",
        back_populates="artifact",
    )


class AIEvidence(Base):
    __tablename__ = "ai_evidence"

    __table_args__ = (
        CheckConstraint(
            "start_char IS NULL OR start_char >= 0",
            name="ck_ai_evidence_start",
        ),
        CheckConstraint(
            "end_char IS NULL OR end_char >= 0",
            name="ck_ai_evidence_end",
        ),
        CheckConstraint(
            "(start_char IS NULL AND end_char IS NULL) OR "
            "(start_char IS NOT NULL AND end_char IS NOT NULL "
            "AND end_char > start_char)",
            name="ck_ai_evidence_offsets",
        ),
    )

    id = Column(Integer, primary_key=True)

    artifact_id = Column(
        Integer,
        ForeignKey("ai_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    source_type = Column(String(50), nullable=False)
    source_id = Column(String(255), nullable=False)
    source_hash = Column(String(64), nullable=True)

    field_path = Column(String(255), nullable=False)
    excerpt = Column(Text, nullable=False)

    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)

    verified = Column(
        Boolean,
        nullable=False,
        default=0,
        server_default="false",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    artifact = relationship(
        "AIArtifact",
        back_populates="evidence",
    )


class AIReviewEvent(Base):
    __tablename__ = "ai_review_events"

    id = Column(Integer, primary_key=True)

    artifact_id = Column(
        Integer,
        ForeignKey("ai_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    reviewer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    action = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)

    before_json = Column(JSONB, nullable=True)
    after_json = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    artifact = relationship(
        "AIArtifact",
        back_populates="review_events",
    )

    reviewer = relationship("User")
