from pydantic import BaseModel, ConfigDict


class DocumentTypeBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_active: bool = True


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class DocumentTypeRead(DocumentTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)