from sqlalchemy.orm import Session

from app.document_types.models import DocumentType
from app.document_types.schemas import (
    DocumentTypeCreate,
    DocumentTypeUpdate,
)


def get_all_document_types(db: Session):
    return (
        db.query(DocumentType)
        .order_by(DocumentType.name.asc())
        .all()
    )


def get_active_document_types(db: Session):
    return (
        db.query(DocumentType)
        .filter(DocumentType.is_active.is_(True))
        .order_by(DocumentType.name.asc())
        .all()
    )


def get_document_type_by_id(
    db: Session,
    document_type_id: int,
):
    return (
        db.query(DocumentType)
        .filter(DocumentType.id == document_type_id)
        .first()
    )


def get_document_type_by_code(
    db: Session,
    code: str,
):
    return (
        db.query(DocumentType)
        .filter(DocumentType.code == code)
        .first()
    )


def create_document_type(
    db: Session,
    document_type_data: DocumentTypeCreate,
):
    document_type = DocumentType(
        **document_type_data.model_dump()
    )

    db.add(document_type)
    db.commit()
    db.refresh(document_type)

    return document_type


def update_document_type(
    db: Session,
    document_type: DocumentType,
    document_type_data: DocumentTypeUpdate,
):
    update_data = document_type_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(document_type, field, value)

    db.commit()
    db.refresh(document_type)

    return document_type


def delete_document_type(
    db: Session,
    document_type: DocumentType,
):
    db.delete(document_type)
    db.commit()