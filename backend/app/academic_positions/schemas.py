from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AcademicPositionBase(BaseModel):
    institution_id: int
    department_id: int

    title: str
    academic_rank_id: int
    field_of_study: str

    description: str

    employment_type_id: int

    application_start_date: date | None = None
    application_deadline: date

    positions_available: int = 1

    position_status_id: int


class AcademicPositionCreate(AcademicPositionBase):
    pass


class AcademicPositionUpdate(BaseModel):
    institution_id: int | None = None
    department_id: int | None = None

    academic_rank_id: int | None = None
    employment_type_id: int | None = None
    position_status_id: int | None = None

    title: str | None = None
    field_of_study: str | None = None
    description: str | None = None

    application_start_date: date | None = None
    application_deadline: date | None = None

    positions_available: int | None = None


class AcademicPositionRead(AcademicPositionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    
    created_by: int
    
    created_at: datetime
    
    updated_at: datetime