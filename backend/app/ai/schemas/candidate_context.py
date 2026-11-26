
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)


class DegreeEvidence(EvidenceRecord):
    degree_type: str
    title: str
    field_of_study: str | None = None
    institution_name: str
    start_year: int | None = None
    end_year: int | None = None


class PublicationEvidence(EvidenceRecord):
    title: str
    publication_year: int | None = None
    publication_type: str | None = None
    doi: str | None = None
    journal_name: str | None = None


class ResearchProjectEvidence(EvidenceRecord):
    title: str
    role: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class TeachingEvidence(EvidenceRecord):
    course_title: str
    institution_name: str | None = None
    academic_year: str | None = None
    teaching_role: str | None = None
    hours_per_week: int | None = None


class CandidateAcademicContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: int = Field(gt=0)
    user_id: int = Field(gt=0)

    specialization: str | None = None
    research_areas: str | None = None

    degrees: list[DegreeEvidence] = Field(default_factory=list)
    publications: list[PublicationEvidence] = Field(
        default_factory=list
    )
    research_projects: list[ResearchProjectEvidence] = Field(
        default_factory=list
    )
    teaching_experience: list[TeachingEvidence] = Field(
        default_factory=list
    )
