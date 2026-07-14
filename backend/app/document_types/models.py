from sqlalchemy import Boolean, Column, Integer, String

from app.core.database import Base


class DocumentType(Base):
    __tablename__ = "document_types"

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

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )