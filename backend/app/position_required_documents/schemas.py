from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PositionRequiredDocumentBase(BaseModel):
    document_type_id: int
    is_required: bool = True
    notes: str | None = None


class PositionRequiredDocumentCreate(
    PositionRequiredDocumentBase
):
    pass


class PositionRequiredDocumentUpdate(BaseModel):
    is_required: bool | None = None
    notes: str | None = None


class PositionRequiredDocumentRead(
    PositionRequiredDocumentBase
):
    id: int
    position_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)