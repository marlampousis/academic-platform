from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


CommitteeStatus = Literal[
    "DRAFT",
    "ACTIVE",
    "COMPLETED",
    "CANCELLED",
]


class EvaluationCommitteeBase(BaseModel):
    position_id: int

    name: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class EvaluationCommitteeCreate(
    EvaluationCommitteeBase
):
    pass


class EvaluationCommitteeUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    status: CommitteeStatus | None = None


class EvaluationCommitteeRead(
    EvaluationCommitteeBase
):
    id: int
    status: CommitteeStatus
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )