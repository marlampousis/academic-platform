from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


EvaluationDecision = Literal[
    "PENDING",
    "SELECTED",
    "NOT_SELECTED",
    "RESERVE",
]


class EvaluationDecisionUpdate(BaseModel):
    decision: EvaluationDecision

    final_comment: str | None = Field(
        default=None,
        max_length=5000,
    )


class EvaluationResultRead(BaseModel):
    id: int
    committee_application_id: int
    final_score: Decimal
    rank_position: int | None
    decision: EvaluationDecision
    final_comment: str | None
    decided_by: int | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class RankingItemRead(BaseModel):
    committee_application_id: int
    application_id: int
    final_score: Decimal
    rank_position: int
    decision: EvaluationDecision | None = None