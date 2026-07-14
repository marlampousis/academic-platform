from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    user_id: int
    profile_id: int | None = None

    file_name: str
    file_path: str
    file_type: str
    document_type_id: int
    upload_status: str

    created_at: datetime

    class Config:
        from_attributes = True
        
class DocumentTextRead(BaseModel):
    id: int
    file_name: str
    upload_status: str
    extracted_text: str | None = None

    class Config:
        from_attributes = True