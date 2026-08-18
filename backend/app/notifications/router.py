from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.users.router import get_current_user
from app.core.database import get_db
from app.notifications.schemas import (
    NotificationRead,
    NotificationUnreadCount,
)
from app.notifications.service import (
    get_notification_by_id,
    get_unread_count,
    get_user_notifications,
    get_user_unread_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)
from app.users.models import User


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "/",
    response_model=list[NotificationRead],
)
def read_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_notifications(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/unread",
    response_model=list[NotificationRead],
)
def read_my_unread_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_unread_notifications(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCount,
)
def read_my_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationUnreadCount(
        unread_count=get_unread_count(
            db=db,
            user_id=current_user.id,
        )
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
)
def mark_my_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = get_notification_by_id(
        db,
        notification_id,
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You cannot access another user's "
                "notification"
            ),
        )

    return mark_notification_as_read(
        db=db,
        notification=notification,
    )


@router.patch(
    "/read-all",
)
def mark_all_my_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_count = (
        mark_all_notifications_as_read(
            db=db,
            user_id=current_user.id,
        )
    )

    return {
        "message": "Notifications marked as read",
        "updated_count": updated_count,
    }