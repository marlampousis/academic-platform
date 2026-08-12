from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    __table_args__ = (
        UniqueConstraint(
            "committee_application_id",
            "reviewer_id",
            name="uq_evaluation_report_assignment_reviewer",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED')",
            name="ck_evaluation_report_status",
        ),
        CheckConstraint(
            "weighted_score >= 0 AND weighted_score <= 100",
            name="ck_evaluation_report_weighted_score",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    committee_application_id = Column(
        Integer,
        ForeignKey(
            "committee_applications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    reviewer_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    weighted_score = Column(
        Numeric(
            precision=6,
            scale=2,
        ),
        nullable=False,
    )

    final_comment = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(20),
        default="DRAFT",
        nullable=False,
    )

    submitted_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    committee_application = relationship(
        "CommitteeApplication",
        back_populates="evaluation_reports",
    )

    reviewer = relationship(
        "User",
        back_populates="evaluation_reports",
    )