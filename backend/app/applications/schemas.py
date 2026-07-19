from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ApplicationStatus = Literal[
    "DRAFT",
    "SUBMITTED",
    "UNDER_REVIEW",
    "ELIGIBLE",
    "REJECTED",
    "WITHDRAWN",
]


class ApplicationCreate(BaseModel):
    position_id: int


class ApplicationRead(BaseModel):
    id: int
    position_id: int
    user_id: int
    profile_id: int

    status: ApplicationStatus
    submitted_at: datetime | None = None

    created_at: datetime
    updated_at: datetime
    
class MissingRequiredDocumentRead(BaseModel):
    document_type_id: int
    document_type_code: str
    document_type_name: str


class ApplicationValidationRead(BaseModel):
    application_id: int
    is_valid: bool
    can_submit: bool

    required_document_count: int
    attached_required_document_count: int

    missing_required_documents: list[
        MissingRequiredDocumentRead
    ]

    errors: list[str]


class ApplicationSubmissionRead(BaseModel):
    id: int
    position_id: int
    user_id: int
    profile_id: int
    status: ApplicationStatus
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime    

    model_config = ConfigDict(from_attributes=True)