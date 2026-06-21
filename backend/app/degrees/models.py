from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Degree(Base):
    __tablename__ = "degrees"

    id = Column(Integer, primary_key=True, index=True)

    profile_id = Column(
        Integer,
        ForeignKey("academic_profiles.id"),
        nullable=False
    )

    degree_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    institution_name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)

    profile = relationship("AcademicProfile")