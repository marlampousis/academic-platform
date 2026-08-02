from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StatusChangedByRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApplicationStatusHistoryRead(BaseModel):
    id: int
    application_id: int
    previous_status: str
    new_status: str
    changed_by: int
    comment: str | None = None
    created_at: datetime

    changed_by_user: StatusChangedByRead

    model_config = ConfigDict(
        from_attributes=True,
    )