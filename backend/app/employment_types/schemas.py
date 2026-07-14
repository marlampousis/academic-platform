from pydantic import BaseModel, ConfigDict


class EmploymentTypeBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class EmploymentTypeCreate(EmploymentTypeBase):
    pass


class EmploymentTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class EmploymentTypeRead(EmploymentTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)