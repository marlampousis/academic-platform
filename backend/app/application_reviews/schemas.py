from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ReviewStatus = Literal[
    "UNDER_REVIEW",
    "ELIGIBLE",
    "REJECTED",
]


class ApplicationStatusUpdate(BaseModel):
    status: ReviewStatus
    
    comment: str | None = Field(
        default=None,
        max_length=1000,
    )


class ApplicationReviewRead(BaseModel):
    id: int
    position_id: int
    profile_id: int
    user_id: int

    status: str
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )