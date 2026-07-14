from pydantic import BaseModel, ConfigDict


class PositionStatusBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class PositionStatusCreate(PositionStatusBase):
    pass


class PositionStatusUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class PositionStatusRead(PositionStatusBase):
    id: int

    model_config = ConfigDict(from_attributes=True)