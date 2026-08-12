from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    __table_args__ = (
        UniqueConstraint(
            "committee_application_id",
            "criterion_id",
            "reviewer_id",
            name="uq_evaluation_score_reviewer_criterion",
        ),
        CheckConstraint(
            "score >= 0",
            name="ck_evaluation_score_non_negative",
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

    criterion_id = Column(
        Integer,
        ForeignKey(
            "evaluation_criteria.id",
            ondelete="RESTRICT",
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

    score = Column(
        Numeric(
            precision=6,
            scale=2,
        ),
        nullable=False,
    )

    comment = Column(
        Text,
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
        back_populates="evaluation_scores",
    )

    criterion = relationship(
        "EvaluationCriterion",
        back_populates="evaluation_scores",
    )

    reviewer = relationship(
        "User",
        back_populates="evaluation_scores",
    )