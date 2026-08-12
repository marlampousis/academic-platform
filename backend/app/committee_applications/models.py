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


class CommitteeApplication(Base):
    __tablename__ = "committee_applications"

    __table_args__ = (
        UniqueConstraint(
            "committee_id",
            "application_id",
            name="uq_committee_application",
        ),
        UniqueConstraint(
            "application_id",
            name="uq_committee_application_application",
        ),
        CheckConstraint(
            "status IN ("
            "'ASSIGNED', "
            "'IN_EVALUATION', "
            "'COMPLETED', "
            "'CANCELLED'"
            ")",
            name="ck_committee_application_status",
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

    application_id = Column(
        Integer,
        ForeignKey(
            "applications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    assigned_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status = Column(
        String(30),
        default="ASSIGNED",
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    assigned_at = Column(
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
        back_populates="assigned_applications",
    )

    application = relationship(
        "Application",
        back_populates="committee_assignment",
    )

    assigner = relationship(
        "User",
        back_populates="assigned_committee_applications",
    )