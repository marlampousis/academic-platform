from typing import Optional

from pydantic import BaseModel, ConfigDict


class AcademicRankBase(BaseModel):
    name: str
    level: int
    description: Optional[str] = None


class AcademicRankCreate(AcademicRankBase):
    pass


class AcademicRankUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    description: Optional[str] = None


class AcademicRankResponse(AcademicRankBase):
    id: int

    model_config = ConfigDict(from_attributes=True)