from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.roles.schemas import RoleRead
from app.roles.service import get_roles


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "/",
    response_model=list[RoleRead],
)
def read_roles(
    db: Session = Depends(get_db),
):
    return get_roles(db)