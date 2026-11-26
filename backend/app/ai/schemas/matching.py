
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RequirementPriority(str, Enum):
    REQUIRED = "REQUIRED"
    DESIRABLE = "DESIRABLE"


class RequirementCategory(str, Enum):
    DEGREE = "DEGREE"
    RESEARCH = "RESEARCH"
    PUBLICATION = "PUBLICATION"
    TEACHING = "TEACHING"
    EXPERIENCE = "EXPERIENCE"
    SPECIALIZATION = "SPECIALIZATION"
    OTHER = "OTHER"


class AcademicRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(min_length=1)
    category: RequirementCategory
    priority: RequirementPriority
    description: str = Field(min_length=1)
    source_excerpt: str = Field(min_length=1)


class PositionRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position_id: int = Field(gt=0)
    position_title: str = Field(min_length=1)
    requirements: list[AcademicRequirement] = Field(
        default_factory=list
    )


class MatchFinding(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceCollection(str, Enum):
    DEGREES = "degrees"
    PUBLICATIONS = "publications"
    RESEARCH_PROJECTS = "research_projects"
    TEACHING_EXPERIENCE = "teaching_experience"


class AcademicEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collection: EvidenceCollection
    record_id: int = Field(gt=0)


class RequirementMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(min_length=1)
    finding: MatchFinding
    explanation: str = Field(min_length=1)
    evidence: list[AcademicEvidenceRef] = Field(
        default_factory=list
    )
    uncertainty: str | None = None


class AcademicMatchingDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: int = Field(gt=0)
    position_id: int = Field(gt=0)
    profile_id: int = Field(gt=0)

    matches: list[RequirementMatch] = Field(
        default_factory=list
    )

    summary: str = Field(min_length=1)
    requires_human_review: bool = True
