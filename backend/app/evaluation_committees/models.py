from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class EvaluationCommittee(Base):
    __tablename__ = "evaluation_committees"

    __table_args__ = (
        UniqueConstraint(
            "position_id",
            name="uq_evaluation_committee_position",
        ),
        CheckConstraint(
            "status IN ("
            "'DRAFT', "
            "'ACTIVE', "
            "'COMPLETED', "
            "'CANCELLED'"
            ")",
            name="ck_evaluation_committee_status",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    position_id = Column(
        Integer,
        ForeignKey(
            "academic_positions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(30),
        default="DRAFT",
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

    position = relationship(
        "AcademicPosition",
    )

    creator = relationship(
        "User",
    )
    
    members = relationship(
        "CommitteeMember",
        back_populates="committee",
        cascade="all, delete-orphan",
    )
    
    assigned_applications = relationship(
        "CommitteeApplication",
        back_populates="committee",
        cascade="all, delete-orphan",
    )
    
    criteria = relationship(
        "EvaluationCriterion",
        back_populates="committee",
        cascade="all, delete-orphan",
        order_by="EvaluationCriterion.display_order",
    )