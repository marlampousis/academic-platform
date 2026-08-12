from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class EvaluationScoreCreate(BaseModel):
    criterion_id: int

    score: Decimal = Field(
        ge=0,
    )

    comment: str | None = Field(
        default=None,
        max_length=3000,
    )


class EvaluationScoreUpdate(BaseModel):
    score: Decimal | None = Field(
        default=None,
        ge=0,
    )

    comment: str | None = Field(
        default=None,
        max_length=3000,
    )


class ScoreCriterionRead(BaseModel):
    id: int
    code: str
    name: str
    weight: Decimal
    max_score: Decimal

    model_config = ConfigDict(
        from_attributes=True,
    )


class ScoreReviewerRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class EvaluationScoreRead(BaseModel):
    id: int

    committee_application_id: int
    criterion_id: int
    reviewer_id: int

    score: Decimal
    comment: str | None

    created_at: datetime
    updated_at: datetime

    criterion: ScoreCriterionRead
    reviewer: ScoreReviewerRead

    model_config = ConfigDict(
        from_attributes=True,
    )