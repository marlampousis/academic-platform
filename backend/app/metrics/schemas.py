from pydantic import BaseModel


class ProfileMetricsRead(BaseModel):
    profile_id: int
    total_publications: int
    total_citations: int
    average_citations: float
    h_index: int