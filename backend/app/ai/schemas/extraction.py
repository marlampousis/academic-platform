
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class IssueType(str, Enum):
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"
    CONTRADICTORY = "CONTRADICTORY"
    UNVERIFIED = "UNVERIFIED"


class EvidenceReference(BaseModel):
    source_id: str
    excerpt: str = Field(min_length=1)
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_offsets(self):
        if (
            self.start_char is not None
            and self.end_char is not None
            and self.end_char <= self.start_char
        ):
            raise ValueError("end_char must be greater than start_char")
        return self


class ExtractionIssue(BaseModel):
    field_path: str
    issue_type: IssueType
    explanation: str


class ExtractedDegree(BaseModel):
    degree_type: str
    title: str
    field_of_study: str | None = None
    institution_name: str
    country: str | None = None
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)

    evidence: list[EvidenceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_years(self):
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.end_year < self.start_year
        ):
            raise ValueError("end_year cannot be before start_year")
        return self


class ExtractedPublication(BaseModel):
    title: str
    abstract: str | None = None
    publication_type: str | None = None
    publication_year: int | None = Field(default=None, ge=1900, le=2100)
    doi: str | None = None
    journal_name: str | None = None
    conference_name: str | None = None
    publisher: str | None = None
    openalex_id: str | None = None
    orcid_work_id: str | None = None

    evidence: list[EvidenceReference] = Field(default_factory=list)


class ExtractedResearchProject(BaseModel):
    title: str
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

    evidence: list[EvidenceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be before start_date")
        return self


class ExtractedTeachingExperience(BaseModel):
    course_title: str
    institution_name: str | None = None
    department_name: str | None = None
    academic_year: str | None = None
    semester: str | None = None
    course_level: str | None = None
    teaching_role: str | None = None
    hours_per_week: int | None = Field(default=None, ge=0, le=80)
    description: str | None = None

    evidence: list[EvidenceReference] = Field(default_factory=list)


class AcademicCVExtraction(BaseModel):
    specialization: str | None = None
    research_areas: str | None = None
    orcid_id: str | None = None
    biography: str | None = None

    degrees: list[ExtractedDegree] = Field(default_factory=list)
    publications: list[ExtractedPublication] = Field(default_factory=list)
    research_projects: list[ExtractedResearchProject] = Field(
        default_factory=list
    )
    teaching_experience: list[ExtractedTeachingExperience] = Field(
        default_factory=list
    )

    issues: list[ExtractionIssue] = Field(default_factory=list)
