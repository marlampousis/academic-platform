from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ResearchProjectCreate(BaseModel):
    title: str
    acronym: str | None = None

    funding_program: str | None = None
    funding_organization: str | None = None

    role: str | None = None
    status: str | None = None

    funding_amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = "EUR"

    start_date: date | None = None
    end_date: date | None = None

    project_identifier: str | None = None
    website_url: str | None = None

    keywords: str | None = None
    description: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, end_date, info):
        start_date = info.data.get("start_date")

        if start_date and end_date and end_date < start_date:
            raise ValueError("end_date cannot be before start_date")

        return end_date


class ResearchProjectUpdate(BaseModel):
    title: str | None = None
    acronym: str | None = None

    funding_program: str | None = None
    funding_organization: str | None = None

    role: str | None = None
    status: str | None = None

    funding_amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None

    start_date: date | None = None
    end_date: date | None = None

    project_identifier: str | None = None
    website_url: str | None = None

    keywords: str | None = None
    description: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, end_date, info):
        start_date = info.data.get("start_date")

        if start_date and end_date and end_date < start_date:
            raise ValueError("end_date cannot be before start_date")

        return end_date


class ResearchProjectRead(BaseModel):
    id: int
    profile_id: int

    title: str
    acronym: str | None = None

    funding_program: str | None = None
    funding_organization: str | None = None

    role: str | None = None
    status: str | None = None

    funding_amount: Decimal | None = None
    currency: str | None = None

    start_date: date | None = None
    end_date: date | None = None

    project_identifier: str | None = None
    website_url: str | None = None

    keywords: str | None = None
    description: str | None = None

    class Config:
        from_attributes = True