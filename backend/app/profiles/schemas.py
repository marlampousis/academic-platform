from pydantic import BaseModel


class AcademicProfileCreate(BaseModel):
    institution_id: int | None = None
    department_id: int | None = None

    academic_rank_id: int | None = None
    specialization: str | None = None
    research_areas: str | None = None
    orcid_id: str | None = None
    biography: str | None = None


class AcademicProfileUpdate(BaseModel):
    institution_id: int | None = None
    department_id: int | None = None

    academic_rank_id: int | None = None
    specialization: str | None = None
    research_areas: str | None = None
    orcid_id: str | None = None
    biography: str | None = None


class AcademicProfileRead(BaseModel):
    id: int

    user_id: int
    institution_id: int | None = None
    department_id: int | None = None

    academic_rank_id: int | None = None
    specialization: str | None = None
    research_areas: str | None = None
    orcid_id: str | None = None
    biography: str | None = None

    class Config:
        from_attributes = True