from sqlalchemy import Column, Integer, String

from app.core.database import Base


class AcademicRank(Base):
    __tablename__ = "academic_ranks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
    )
    
    level = Column(
        Integer,
        nullable=False,
        unique=True,
    )

    description = Column(
        String(255),
        nullable=True,
    )