from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "document_id",
            name="uq_application_document",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    application_id = Column(
        Integer,
        ForeignKey(
            "applications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    source = Column(
        String(50),
        default="PROFILE",
        nullable=False,
    )

    attached_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    application = relationship("Application")
    document = relationship("Document")