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


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    __table_args__ = (
        UniqueConstraint(
            "committee_application_id",
            name="uq_evaluation_result_application",
        ),
        CheckConstraint(
            "final_score >= 0 AND final_score <= 100",
            name="ck_evaluation_result_score",
        ),
        CheckConstraint(
            "decision IN ("
            "'PENDING', "
            "'SELECTED', "
            "'NOT_SELECTED', "
            "'RESERVE'"
            ")",
            name="ck_evaluation_result_decision",
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
        unique=True,
        index=True,
    )

    final_score = Column(
        Numeric(
            precision=6,
            scale=2,
        ),
        nullable=False,
    )

    rank_position = Column(
        Integer,
        nullable=True,
    )

    decision = Column(
        String(30),
        default="PENDING",
        nullable=False,
    )

    final_comment = Column(
        Text,
        nullable=True,
    )

    decided_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    decided_at = Column(
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
        back_populates="evaluation_result",
    )

    decision_maker = relationship(
        "User",
        back_populates="evaluation_decisions",
    )