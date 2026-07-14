from sqlalchemy import Column, Integer, String

from app.core.database import Base


class PositionStatus(Base):
    __tablename__ = "position_statuses"

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