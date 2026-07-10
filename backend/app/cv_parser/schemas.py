from pydantic import BaseModel


class ParsedCVPreview(BaseModel):
    orcid_ids: list[str] = []
    dois: list[str] = []
    education_section: str | None = None
    publications_section: str | None = None
    research_projects_section: str | None = None
    teaching_section: str | None = None
    
    
class ParsedDegree(BaseModel):
    title: str
    institution: str | None = None
    year: int | None = None


class ParsedPublication(BaseModel):
    title: str
    doi: str | None = None


class ParsedTeaching(BaseModel):
    course: str


class ParsedResearchProject(BaseModel):
    title: str


class StructuredCVPreview(BaseModel):
    orcid_ids: list[str] = []

    dois: list[str] = []

    degrees: list[ParsedDegree] = []

    publications: list[ParsedPublication] = []

    research_projects: list[ParsedResearchProject] = []

    teaching_experience: list[ParsedTeaching] = []    
    
class CVImportResponse(BaseModel):
    profile_updated: bool

    degrees_imported: int
    degrees_skipped: int

    publications_imported: int
    publications_skipped: int

    research_projects_imported: int
    research_projects_skipped: int

    teaching_imported: int
    teaching_skipped: int

    document_status: str    