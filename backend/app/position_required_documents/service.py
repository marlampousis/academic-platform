from sqlalchemy.orm import Session

from app.position_required_documents.models import (
    PositionRequiredDocument,
)
from app.position_required_documents.schemas import (
    PositionRequiredDocumentCreate,
    PositionRequiredDocumentUpdate,
)


def get_required_documents_by_position(
    db: Session,
    position_id: int,
):
    return (
        db.query(PositionRequiredDocument)
        .filter(
            PositionRequiredDocument.position_id
            == position_id
        )
        .order_by(PositionRequiredDocument.id.asc())
        .all()
    )


def get_required_document_by_id(
    db: Session,
    required_document_id: int,
):
    return (
        db.query(PositionRequiredDocument)
        .filter(
            PositionRequiredDocument.id
            == required_document_id
        )
        .first()
    )


def get_required_document_by_type(
    db: Session,
    position_id: int,
    document_type_id: int,
):
    return (
        db.query(PositionRequiredDocument)
        .filter(
            PositionRequiredDocument.position_id
            == position_id,
            PositionRequiredDocument.document_type_id
            == document_type_id,
        )
        .first()
    )


def create_required_document(
    db: Session,
    position_id: int,
    required_document_data: PositionRequiredDocumentCreate,
):
    required_document = PositionRequiredDocument(
        position_id=position_id,
        **required_document_data.model_dump(),
    )

    db.add(required_document)
    db.commit()
    db.refresh(required_document)

    return required_document


def update_required_document(
    db: Session,
    required_document: PositionRequiredDocument,
    required_document_data: PositionRequiredDocumentUpdate,
):
    update_data = required_document_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(required_document, field, value)

    db.commit()
    db.refresh(required_document)

    return required_document


def delete_required_document(
    db: Session,
    required_document: PositionRequiredDocument,
):
    db.delete(required_document)
    db.commit()