from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "position_id",
            name="uq_application_user_position",
        ),
        CheckConstraint(
            "status IN ("
            "'DRAFT', "
            "'SUBMITTED', "
            "'UNDER_REVIEW', "
            "'ELIGIBLE', "
            "'REJECTED', "
            "'WITHDRAWN'"
            ")",
            name="ck_application_status",
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
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    profile_id = Column(
        Integer,
        ForeignKey(
            "academic_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    status = Column(
        String(30),
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

    position = relationship("AcademicPosition")
    user = relationship("User")
    profile = relationship("AcademicProfile")