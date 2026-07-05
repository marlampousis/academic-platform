from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class TeachingExperience(Base):
    __tablename__ = "teaching_experience"

    id = Column(Integer, primary_key=True, index=True)

    profile_id = Column(
        Integer,
        ForeignKey("academic_profiles.id"),
        nullable=False
    )

    course_title = Column(String(255), nullable=False)
    institution_name = Column(String(255), nullable=True)
    department_name = Column(String(255), nullable=True)

    academic_year = Column(String(20), nullable=True)
    semester = Column(String(50), nullable=True)
    course_level = Column(String(100), nullable=True)
    teaching_role = Column(String(100), nullable=True)

    hours_per_week = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    profile = relationship("AcademicProfile")