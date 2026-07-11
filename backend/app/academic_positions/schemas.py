from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AcademicPositionBase(BaseModel):
    institution_id: int
    department_id: int

    title: str
    academic_rank: str
    field_of_study: str

    description: str

    employment_type: str

    application_start_date: date | None = None
    application_deadline: date

    positions_available: int = 1

    status: str = "OPEN"


class AcademicPositionCreate(AcademicPositionBase):
    pass


class AcademicPositionUpdate(BaseModel):
    title: str | None = None
    academic_rank: str | None = None
    field_of_study: str | None = None
    description: str | None = None
    employment_type: str | None = None
    application_start_date: date | None = None
    application_deadline: date | None = None
    positions_available: int | None = None
    status: str | None = None


class AcademicPositionRead(AcademicPositionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    created_by: int

    created_at: datetime

    updated_at: datetime