from pydantic import BaseModel


class OrcidProfilePreview(BaseModel):
    orcid_id: str
    given_names: str | None = None
    family_name: str | None = None
    credit_name: str | None = None
    biography: str | None = None


class OrcidWorkPreview(BaseModel):
    title: str | None = None
    publication_year: int | None = None
    doi: str | None = None
    work_type: str | None = None
    journal_title: str | None = None
    orcid_work_id: str | None = None
    
class OrcidImportWorksResponse(BaseModel):
    imported_count: int
    skipped_count: int
    
class OrcidEducationPreview(BaseModel):
    organization_name: str | None = None
    department_name: str | None = None
    role_title: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    orcid_education_id: str | None = None


class OrcidImportEducationResponse(BaseModel):
    imported_count: int
    skipped_count: int
    
class OrcidImportProfileResponse(BaseModel):
    message: str
    orcid_id: str
    
class OrcidSyncResponse(BaseModel):
    message: str
    orcid_id: str
    works_imported: int
    works_skipped: int
    education_imported: int
    education_skipped: int                