from datetime import date

from sqlalchemy.orm import Session

from app.applications.models import Application
from app.academic_positions.models import AcademicPosition
from app.notifications.models import Notification
from app.notifications.service import (
    notify_deadline_reminder,
)


REMINDER_DAYS = {7, 3, 1}
#REMINDER_DAYS = {7, 6, 5, 4, 3, 2, 1}

def process_deadline_reminders(
    db: Session,
) -> list:
    today = date.today()

    draft_applications = (
        db.query(Application)
        .filter(
            Application.status == "DRAFT"
        )
        .all()
    )

    created_notifications = []

    for application in draft_applications:
        position = (
            db.query(AcademicPosition)
            .filter(
                AcademicPosition.id
                == application.position_id
            )
            .first()
        )

        if not position:
            continue

        days_remaining = (
            position.application_deadline - today
        ).days

        if days_remaining not in REMINDER_DAYS:
            continue

        dedup_key = (
            f"deadline:{application.id}:"
            f"{days_remaining}"
        )

        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.dedup_key == dedup_key
            )
            .first()
        )

        if existing_notification:
            continue
    
        notification = notify_deadline_reminder(
            db=db,
            user_id=application.user_id,
            position_id=position.id,
            days_remaining=days_remaining,
            dedup_key=dedup_key,
        )

        created_notifications.append(
            notification
        )

    return created_notifications