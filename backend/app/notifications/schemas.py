from datetime import datetime

from app.notifications.types import NotificationType

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class NotificationCreate(BaseModel):
    user_id: int

    type: NotificationType

    title: str = Field(
        min_length=2,
        max_length=255,
    )

    message: str = Field(
        min_length=1,
        max_length=5000,
    )


class NotificationRead(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class NotificationUnreadCount(BaseModel):
    unread_count: int