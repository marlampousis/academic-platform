from sqlalchemy.orm import Session

from app.applications.models import Application

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.application_documents.models import ApplicationDocument
from app.documents.models import Document
from app.position_required_documents.models import PositionRequiredDocument

def create_application(
    db: Session,
    position_id: int,
    user_id: int,
    profile_id: int,
):
    application = Application(
        position_id=position_id,
        user_id=user_id,
        profile_id=profile_id,
        status="DRAFT",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


def get_application_by_id(
    db: Session,
    application_id: int,
):
    return (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )


def get_application_by_user_and_position(
    db: Session,
    user_id: int,
    position_id: int,
):
    return (
        db.query(Application)
        .filter(
            Application.user_id == user_id,
            Application.position_id == position_id,
        )
        .first()
    )


def get_applications_by_user_id(
    db: Session,
    user_id: int,
):
    return (
        db.query(Application)
        .filter(Application.user_id == user_id)
        .order_by(Application.created_at.desc())
        .all()
    )


def delete_application(
    db: Session,
    application: Application,
):
    db.delete(application)
    db.commit()
    
def validate_application(
    db: Session,
    application: Application,
):
    errors = []

    position = application.position

    if application.status != "DRAFT":
        errors.append(
            "Only draft applications can be submitted"
        )

    if (
        not position.position_status
        or position.position_status.code != "OPEN"
    ):
        errors.append(
            "Position is not open"
        )

    today = date.today()

    if (
        position.application_start_date
        and today < position.application_start_date
    ):
        errors.append(
            "Application period has not started yet"
        )

    if (
        position.application_deadline
        and today > position.application_deadline
    ):
        errors.append(
            "Application deadline has passed"
        )

    required_documents = (
        db.query(PositionRequiredDocument)
        .filter(
            PositionRequiredDocument.position_id
            == application.position_id,
            PositionRequiredDocument.is_required.is_(True),
        )
        .all()
    )

    attached_document_type_ids = {
        document_type_id
        for (document_type_id,) in (
            db.query(Document.document_type_id)
            .join(
                ApplicationDocument,
                ApplicationDocument.document_id
                == Document.id,
            )
            .filter(
                ApplicationDocument.application_id
                == application.id
            )
            .all()
        )
    }

    missing_required_documents = []

    for required_document in required_documents:
        if (
            required_document.document_type_id
            not in attached_document_type_ids
        ):
            document_type = required_document.document_type

            missing_required_documents.append(
                {
                    "document_type_id": document_type.id,
                    "document_type_code": document_type.code,
                    "document_type_name": document_type.name,
                }
            )

    required_document_count = len(
        required_documents
    )

    attached_required_document_count = (
        required_document_count
        - len(missing_required_documents)
    )

    if missing_required_documents:
        errors.append(
            "Required documents are missing"
        )

    can_submit = (
        len(errors) == 0
        and len(missing_required_documents) == 0
    )

    return {
        "application_id": application.id,
        "is_valid": can_submit,
        "can_submit": can_submit,
        "required_document_count": (
            required_document_count
        ),
        "attached_required_document_count": (
            attached_required_document_count
        ),
        "missing_required_documents": (
            missing_required_documents
        ),
        "errors": errors,
    }


def submit_application(
    db: Session,
    application: Application,
):
    application.status = "SUBMITTED"
    application.submitted_at = datetime.utcnow()
    application.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(application)

    return application    