from pydantic import BaseModel


class InstitutionRead(BaseModel):
    id: int
    name_el: str
    name_en: str | None = None
    short_name: str | None = None
    institution_type: str
    country: str
    city: str | None = None
    website_url: str | None = None
    is_active: bool

    class Config:
        from_attributes = True