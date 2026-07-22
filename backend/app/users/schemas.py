from pydantic import BaseModel, EmailStr, Field
from app.roles.schemas import RoleRead

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role_id: int
    role: RoleRead

    class Config:
        from_attributes = True