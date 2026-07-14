from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PositionRequiredDocument(Base):
    __tablename__ = "position_required_documents"

    __table_args__ = (
        UniqueConstraint(
            "position_id",
            "document_type_id",
            name="uq_position_required_document_type",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    position_id = Column(
        Integer,
        ForeignKey(
            "academic_positions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    document_type_id = Column(
        Integer,
        ForeignKey("document_types.id"),
        nullable=False,
    )

    is_required = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    notes = Column(
        String(500),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    position = relationship("AcademicPosition")
    document_type = relationship("DocumentType")