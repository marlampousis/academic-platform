from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    institution_id: int
    name_el: str
    name_en: str | None = None
    department_type: str = "DEPARTMENT"
    city: str | None = None
    website_url: str | None = None


class DepartmentRead(BaseModel):
    id: int
    institution_id: int
    name_el: str
    name_en: str | None = None
    department_type: str
    city: str | None = None
    website_url: str | None = None
    is_active: bool

    class Config:
        from_attributes = True