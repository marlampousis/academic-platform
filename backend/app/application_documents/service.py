from sqlalchemy.orm import Session

from app.application_documents.models import (
    ApplicationDocument,
)


def create_application_document(
    db: Session,
    application_id: int,
    document_id: int,
    source: str = "PROFILE",
):
    application_document = ApplicationDocument(
        application_id=application_id,
        document_id=document_id,
        source=source,
    )

    db.add(application_document)
    db.commit()
    db.refresh(application_document)

    return application_document


def get_application_documents(
    db: Session,
    application_id: int,
):
    return (
        db.query(ApplicationDocument)
        .filter(
            ApplicationDocument.application_id
            == application_id
        )
        .order_by(
            ApplicationDocument.attached_at.asc()
        )
        .all()
    )


def get_application_document_by_id(
    db: Session,
    application_document_id: int,
):
    return (
        db.query(ApplicationDocument)
        .filter(
            ApplicationDocument.id
            == application_document_id
        )
        .first()
    )


def get_application_document_by_document(
    db: Session,
    application_id: int,
    document_id: int,
):
    return (
        db.query(ApplicationDocument)
        .filter(
            ApplicationDocument.application_id
            == application_id,
            ApplicationDocument.document_id
            == document_id,
        )
        .first()
    )


def delete_application_document(
    db: Session,
    application_document: ApplicationDocument,
):
    db.delete(application_document)
    db.commit()