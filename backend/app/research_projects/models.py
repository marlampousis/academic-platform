from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True)

    profile_id = Column(
        Integer,
        ForeignKey("academic_profiles.id"),
        nullable=False
    )

    title = Column(String(500), nullable=False)
    acronym = Column(String(100), nullable=True)

    funding_program = Column(String(255), nullable=True)
    funding_organization = Column(String(255), nullable=True)

    role = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True)

    funding_amount = Column(Numeric(15, 2), nullable=True)
    currency = Column(String(10), nullable=True, default="EUR")

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    project_identifier = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)

    keywords = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    profile = relationship("AcademicProfile")