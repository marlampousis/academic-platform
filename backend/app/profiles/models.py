from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class AcademicProfile(Base):
    __tablename__ = "academic_profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    academic_rank = Column(String(100), nullable=True)
    specialization = Column(String(255), nullable=True)
    research_areas = Column(Text, nullable=True)
    orcid_id = Column(String(50), nullable=True)
    biography = Column(Text, nullable=True)

    user = relationship("User")
    institution = relationship("Institution")
    department = relationship("Department")