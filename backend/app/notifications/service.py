from datetime import datetime

from sqlalchemy.orm import Session

from app.notifications.models import Notification
from app.notifications.types import NotificationType

def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type.value,
        title=title,
        message=message,
        is_read=False,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_user_notifications(
    db: Session,
    user_id: int,
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .all()
    )


def get_user_unread_notifications(
    db: Session,
    user_id: int,
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .all()
    )


def get_notification_by_id(
    db: Session,
    notification_id: int,
) -> Notification | None:
    return (
        db.query(Notification)
        .filter(
            Notification.id == notification_id
        )
        .first()
    )


def get_unread_count(
    db: Session,
    user_id: int,
) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .count()
    )


def mark_notification_as_read(
    db: Session,
    notification: Notification,
) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()

        db.commit()
        db.refresh(notification)

    return notification


def mark_all_notifications_as_read(
    db: Session,
    user_id: int,
) -> int:
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .all()
    )

    now = datetime.utcnow()

    for notification in notifications:
        notification.is_read = True
        notification.read_at = now

    db.commit()

    return len(notifications)

def notify_application_submitted(
    db: Session,
    user_id: int,
    application_id: int,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.APPLICATION_SUBMITTED,
        title="Application submitted",
        message=(
            f"Your application #{application_id} "
            "was successfully submitted."
        ),
    )
    
def notify_application_status_changed(
    db: Session,
    user_id: int,
    application_id: int,
    new_status: str,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=(
            NotificationType.APPLICATION_STATUS_CHANGED
        ),
        title="Application status updated",
        message=(
            f"Your application #{application_id} "
            f"is now {new_status}."
        ),
    )
    
def notify_missing_documents(
    db: Session,
    user_id: int,
    application_id: int,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.MISSING_DOCUMENTS,
        title="Missing required documents",
        message=(
            f"Application #{application_id} "
            "is missing one or more required documents."
        ),
    )
    
def notify_application_assigned(
    db: Session,
    user_id: int,
    application_id: int,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.APPLICATION_ASSIGNED,
        title="Application assigned for evaluation",
        message=(
            f"Application #{application_id} "
            "has been assigned to your evaluation committee."
        ),
    )            
    
def notify_evaluation_started(
    db: Session,
    user_id: int,
    application_id: int,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.EVALUATION_STARTED,
        title="Evaluation started",
        message=(
            f"The evaluation of application "
            f"#{application_id} has started."
        ),
    )
    
def notify_evaluation_completed(
    db: Session,
    user_id: int,
    application_id: int,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.EVALUATION_COMPLETED,
        title="Evaluation completed",
        message=(
            f"The evaluation of application "
            f"#{application_id} has been completed."
        ),
    )
    
def notify_final_decision(
    db: Session,
    user_id: int,
    application_id: int,
    decision: str,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.FINAL_DECISION,
        title="Final application decision",
        message=(
            f"A final decision has been recorded "
            f"for application #{application_id}: "
            f"{decision}."
        ),
    )
    
def notify_deadline_reminder(
    db: Session,
    user_id: int,
    position_id: int,
    days_remaining: int,
) -> Notification:
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.DEADLINE_REMINDER,
        title="Application deadline reminder",
        message=(
            f"The deadline for position "
            f"#{position_id} is in "
            f"{days_remaining} day(s)."
        ),
    )                