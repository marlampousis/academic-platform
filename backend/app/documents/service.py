from sqlalchemy.orm import Session

from app.documents.models import Document


def create_document(
    db: Session,
    user_id: int,
    profile_id: int | None,
    file_name: str,
    file_path: str,
    file_type: str,
    document_type: str = "CV"
):
    document = Document(
        user_id=user_id,
        profile_id=profile_id,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        document_type=document_type,
        upload_status="UPLOADED"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_documents_by_user_id(db: Session, user_id: int):
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    
def get_document_by_id(db: Session, document_id: int):
    return (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )


def update_document_extracted_text(
    db: Session,
    document: Document,
    extracted_text: str
):
    document.extracted_text = extracted_text
    document.upload_status = "TEXT_EXTRACTED"

    db.commit()
    db.refresh(document)

    return document


def update_document_status(
    db: Session,
    document: Document,
    status_value: str
):
    document.upload_status = status_value

    db.commit()
    db.refresh(document)

    return document