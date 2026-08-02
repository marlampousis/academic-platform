from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


CommitteeMemberRole = Literal[
    "CHAIR",
    "MEMBER",
    "SECRETARY",
]


class CommitteeMemberCreate(BaseModel):
    user_id: int
    role_in_committee: CommitteeMemberRole = "MEMBER"


class CommitteeMemberUpdate(BaseModel):
    role_in_committee: CommitteeMemberRole | None = None
    is_active: bool | None = None


class CommitteeMemberUserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CommitteeMemberRead(BaseModel):
    id: int
    committee_id: int
    user_id: int
    role_in_committee: CommitteeMemberRole
    is_active: bool
    joined_at: datetime

    user: CommitteeMemberUserRead

    model_config = ConfigDict(
        from_attributes=True,
    )