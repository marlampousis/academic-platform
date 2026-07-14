from sqlalchemy import Column, Integer, String

from app.core.database import Base


class EmploymentType(Base):
    __tablename__ = "employment_types"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    description = Column(
        String(255),
        nullable=True,
    )