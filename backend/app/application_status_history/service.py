from sqlalchemy.orm import Session, joinedload

from app.application_status_history.models import (
    ApplicationStatusHistory,
)


def create_status_history_entry(
    db: Session,
    application_id: int,
    previous_status: str,
    new_status: str,
    changed_by: int,
    comment: str | None = None,
) -> ApplicationStatusHistory:
    history_entry = ApplicationStatusHistory(
        application_id=application_id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=changed_by,
        comment=comment,
    )

    db.add(history_entry)

    return history_entry


def get_application_status_history(
    db: Session,
    application_id: int,
) -> list[ApplicationStatusHistory]:
    return (
        db.query(ApplicationStatusHistory)
        .options(
            joinedload(
                ApplicationStatusHistory.changed_by_user
            )
        )
        .filter(
            ApplicationStatusHistory.application_id
            == application_id
        )
        .order_by(
            ApplicationStatusHistory.created_at.asc(),
            ApplicationStatusHistory.id.asc(),
        )
        .all()
    )