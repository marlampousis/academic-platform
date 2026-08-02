from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class CommitteeMember(Base):
    __tablename__ = "committee_members"

    __table_args__ = (
        UniqueConstraint(
            "committee_id",
            "user_id",
            name="uq_committee_member_user",
        ),
        CheckConstraint(
            "role_in_committee IN ("
            "'CHAIR', "
            "'MEMBER', "
            "'SECRETARY'"
            ")",
            name="ck_committee_member_role",
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

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    role_in_committee = Column(
        String(30),
        default="MEMBER",
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    joined_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    committee = relationship(
        "EvaluationCommittee",
        back_populates="members",
    )

    user = relationship(
        "User",
        back_populates="committee_memberships",
    )