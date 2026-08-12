from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


EvaluationReportStatus = Literal[
    "DRAFT",
    "SUBMITTED",
]


class EvaluationReportCreate(BaseModel):
    final_comment: str | None = Field(
        default=None,
        max_length=5000,
    )


class EvaluationReportUpdate(BaseModel):
    final_comment: str | None = Field(
        default=None,
        max_length=5000,
    )


class EvaluationReportReviewerRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class EvaluationReportRead(BaseModel):
    id: int
    committee_application_id: int
    reviewer_id: int
    weighted_score: Decimal
    final_comment: str | None
    status: EvaluationReportStatus
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    reviewer: EvaluationReportReviewerRead

    model_config = ConfigDict(
        from_attributes=True,
    )