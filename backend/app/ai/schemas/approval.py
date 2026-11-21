
from pydantic import BaseModel, Field


class ExtractionApprovalRequest(BaseModel):
    expected_version: int = Field(ge=1)
    confirm: bool
