from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.applications.models import Application
from app.application_status_history.service import create_status_history_entry


ALLOWED_STATUS_TRANSITIONS = {
    "SUBMITTED": {
        "UNDER_REVIEW",
    },
    "UNDER_REVIEW": {
        "ELIGIBLE",
        "REJECTED",
    },
}


def get_applications_for_position(
    db: Session,
    position_id: int,
    application_status: str | None = None,
) -> list[Application]:
    query = (
        db.query(Application)
        .filter(
            Application.position_id == position_id
        )
    )

    if application_status:
        query = query.filter(
            Application.status
            == application_status.strip().upper()
        )

    return (
        query
        .order_by(Application.created_at.desc())
        .all()
    )


def get_application_for_review(
    db: Session,
    application_id: int,
) -> Application:
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    return application


def validate_status_transition(
    current_status: str,
    new_status: str,
) -> None:
    normalized_current_status = (
        current_status.strip().upper()
    )

    normalized_new_status = (
        new_status.strip().upper()
    )

    allowed_next_statuses = (
        ALLOWED_STATUS_TRANSITIONS.get(
            normalized_current_status,
            set(),
        )
    )

    if normalized_new_status not in allowed_next_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid application status transition: "
                f"{normalized_current_status} -> "
                f"{normalized_new_status}"
            ),
        )


def update_application_review_status(
    db: Session,
    application: Application,
    new_status: str,
    changed_by: int,
    comment: str | None = None,
) -> Application:
    normalized_status = (
        new_status.strip().upper()
    )

    current_status = (
        application.status.strip().upper()
    )

    validate_status_transition(
        current_status=current_status,
        new_status=normalized_status,
    )

    create_status_history_entry(
        db=db,
        application_id=application.id,
        previous_status=current_status,
        new_status=normalized_status,
        changed_by=changed_by,
        comment=comment,
    )

    application.status = normalized_status
    application.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(application)

    except Exception:
        db.rollback()
        raise

    return application