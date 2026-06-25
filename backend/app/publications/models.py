from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)

    profile_id = Column(
        Integer,
        ForeignKey("academic_profiles.id"),
        nullable=False
    )

    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=True)

    publication_type = Column(String(100), nullable=True)
    publication_year = Column(Integer, nullable=True)

    doi = Column(String(255), nullable=True)
    journal_name = Column(String(255), nullable=True)
    conference_name = Column(String(255), nullable=True)
    publisher = Column(String(255), nullable=True)

    citation_count = Column(Integer, nullable=True, default=0)

    openalex_id = Column(String(255), nullable=True)
    orcid_work_id = Column(String(255), nullable=True)

    profile = relationship("AcademicProfile")