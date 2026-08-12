from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


CommitteeApplicationStatus = Literal[
    "ASSIGNED",
    "IN_EVALUATION",
    "COMPLETED",
    "CANCELLED",
]


class CommitteeApplicationCreate(BaseModel):
    application_id: int

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class CommitteeApplicationUpdate(BaseModel):
    status: CommitteeApplicationStatus | None = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class AssignedApplicationRead(BaseModel):
    id: int
    position_id: int
    user_id: int
    profile_id: int
    status: str
    submitted_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class CommitteeApplicationRead(BaseModel):
    id: int
    committee_id: int
    application_id: int
    assigned_by: int
    status: CommitteeApplicationStatus
    notes: str | None = None
    assigned_at: datetime
    updated_at: datetime

    application: AssignedApplicationRead

    model_config = ConfigDict(
        from_attributes=True,
    )