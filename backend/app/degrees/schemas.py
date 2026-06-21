from pydantic import BaseModel, Field


class DegreeCreate(BaseModel):
    degree_type: str
    title: str
    field_of_study: str | None = None
    institution_name: str
    country: str | None = None
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)


class DegreeRead(BaseModel):
    id: int
    profile_id: int
    degree_type: str
    title: str
    field_of_study: str | None = None
    institution_name: str
    country: str | None = None
    start_year: int | None = None
    end_year: int | None = None

    class Config:
        from_attributes = True