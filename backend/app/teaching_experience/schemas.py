from pydantic import BaseModel, Field


class TeachingExperienceCreate(BaseModel):
    course_title: str
    institution_name: str | None = None
    department_name: str | None = None

    academic_year: str | None = None
    semester: str | None = None
    course_level: str | None = None
    teaching_role: str | None = None

    hours_per_week: int | None = Field(default=None, ge=0, le=80)
    description: str | None = None


class TeachingExperienceUpdate(BaseModel):
    course_title: str | None = None
    institution_name: str | None = None
    department_name: str | None = None

    academic_year: str | None = None
    semester: str | None = None
    course_level: str | None = None
    teaching_role: str | None = None

    hours_per_week: int | None = Field(default=None, ge=0, le=80)
    description: str | None = None


class TeachingExperienceRead(BaseModel):
    id: int
    profile_id: int

    course_title: str
    institution_name: str | None = None
    department_name: str | None = None

    academic_year: str | None = None
    semester: str | None = None
    course_level: str | None = None
    teaching_role: str | None = None

    hours_per_week: int | None = None
    description: str | None = None

    class Config:
        from_attributes = True