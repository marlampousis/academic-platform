from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class EvaluationCriterionCreate(BaseModel):
    code: str = Field(
        min_length=2,
        max_length=50,
    )

    name: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    weight: Decimal = Field(
        gt=0,
        le=100,
    )

    max_score: Decimal = Field(
        default=Decimal("10"),
        gt=0,
    )

    display_order: int = Field(
        default=0,
        ge=0,
    )

    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(
        cls,
        value: str,
    ) -> str:
        return (
            value.strip()
            .upper()
            .replace(" ", "_")
        )


class EvaluationCriterionUpdate(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    weight: Decimal | None = Field(
        default=None,
        gt=0,
        le=100,
    )

    max_score: Decimal | None = Field(
        default=None,
        gt=0,
    )

    display_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return (
            value.strip()
            .upper()
            .replace(" ", "_")
        )


class EvaluationCriterionRead(BaseModel):
    id: int
    committee_id: int
    code: str
    name: str
    description: str | None
    weight: Decimal
    max_score: Decimal
    display_order: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class EvaluationCriteriaSummary(BaseModel):
    committee_id: int
    criteria_count: int
    active_criteria_count: int
    total_active_weight: Decimal
    is_weight_complete: bool
    criteria: list[EvaluationCriterionRead]