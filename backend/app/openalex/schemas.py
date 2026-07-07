from pydantic import BaseModel


class OpenAlexWorkPreview(BaseModel):
    openalex_id: str | None = None
    title: str | None = None
    publication_year: int | None = None
    doi: str | None = None
    publication_type: str | None = None
    journal_name: str | None = None
    citation_count: int | None = 0
    authors: list[str] = []
    
class OpenAlexImportRequest(BaseModel):
    openalex_id: str    