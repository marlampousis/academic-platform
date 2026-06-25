from pydantic import BaseModel, Field


class PublicationCreate(BaseModel):
    title: str
    abstract: str | None = None

    publication_type: str | None = None
    publication_year: int | None = Field(default=None, ge=1900, le=2100)

    doi: str | None = None
    journal_name: str | None = None
    conference_name: str | None = None
    publisher: str | None = None

    citation_count: int | None = Field(default=0, ge=0)

    openalex_id: str | None = None
    orcid_work_id: str | None = None


class PublicationUpdate(BaseModel):
    title: str | None = None
    abstract: str | None = None

    publication_type: str | None = None
    publication_year: int | None = Field(default=None, ge=1900, le=2100)

    doi: str | None = None
    journal_name: str | None = None
    conference_name: str | None = None
    publisher: str | None = None

    citation_count: int | None = Field(default=None, ge=0)

    openalex_id: str | None = None
    orcid_work_id: str | None = None


class PublicationRead(BaseModel):
    id: int
    profile_id: int

    title: str
    abstract: str | None = None

    publication_type: str | None = None
    publication_year: int | None = None

    doi: str | None = None
    journal_name: str | None = None
    conference_name: str | None = None
    publisher: str | None = None

    citation_count: int | None = None

    openalex_id: str | None = None
    orcid_work_id: str | None = None

    class Config:
        from_attributes = True