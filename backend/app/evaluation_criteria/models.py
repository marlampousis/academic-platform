from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class EvaluationCriterion(Base):
    __tablename__ = "evaluation_criteria"

    __table_args__ = (
        UniqueConstraint(
            "committee_id",
            "code",
            name="uq_evaluation_criterion_committee_code",
        ),
        CheckConstraint(
            "weight > 0 AND weight <= 100",
            name="ck_evaluation_criterion_weight",
        ),
        CheckConstraint(
            "max_score > 0",
            name="ck_evaluation_criterion_max_score",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="ck_evaluation_criterion_display_order",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    committee_id = Column(
        Integer,
        ForeignKey(
            "evaluation_committees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code = Column(
        String(50),
        nullable=False,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    weight = Column(
        Numeric(
            precision=5,
            scale=2,
        ),
        nullable=False,
    )

    max_score = Column(
        Numeric(
            precision=6,
            scale=2,
        ),
        default=10,
        nullable=False,
    )

    display_order = Column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
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

    committee = relationship(
        "EvaluationCommittee",
        back_populates="criteria",
    )

    creator = relationship(
        "User",
        back_populates="created_evaluation_criteria",
    )