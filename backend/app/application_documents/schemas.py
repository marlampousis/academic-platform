from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ApplicationDocumentSource = Literal[
    "PROFILE",
    "APPLICATION_UPLOAD",
    "AUTO_GENERATED",
]


class ApplicationDocumentCreate(BaseModel):
    document_id: int


class ApplicationDocumentRead(BaseModel):
    id: int
    application_id: int
    document_id: int
    source: ApplicationDocumentSource
    attached_at: datetime

    model_config = ConfigDict(from_attributes=True)