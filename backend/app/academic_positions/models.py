from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class AcademicPosition(Base):
    __tablename__ = "academic_positions"

    id = Column(Integer, primary_key=True, index=True)

    institution_id = Column(
        Integer,
        ForeignKey("institutions.id"),
        nullable=False
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(String(255), nullable=False)

    academic_rank_id = Column(
        Integer,
        ForeignKey("academic_ranks.id"),
        nullable=False,
    )

    field_of_study = Column(String(255), nullable=False)

    description = Column(Text, nullable=False)

    employment_type_id = Column(
        Integer,
        ForeignKey("employment_types.id"),
        nullable=False,
    )
    
    application_start_date = Column(
        Date,
        nullable=True
    )

    positions_available = Column(
        Integer,
        default=1,
        nullable=False
    )

    application_deadline = Column(
        Date,
        nullable=False
    )

    position_status_id = Column(
        Integer,
        ForeignKey("position_statuses.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    institution = relationship("Institution")

    department = relationship("Department")

    creator = relationship("User")
    
    academic_rank = relationship("AcademicRank")
    employment_type = relationship("EmploymentType")
    position_status = relationship("PositionStatus")