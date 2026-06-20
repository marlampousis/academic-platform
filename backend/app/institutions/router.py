from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.institutions.schemas import InstitutionRead
from app.institutions.service import get_institutions, get_institution_by_id

from app.departments.schemas import DepartmentRead
from app.departments.service import get_departments_by_institution

router = APIRouter(
    prefix="/institutions",
    tags=["Institutions"]
)


@router.get("/", response_model=list[InstitutionRead])
def read_institutions(db: Session = Depends(get_db)):
    return get_institutions(db)


@router.get("/{institution_id}", response_model=InstitutionRead)
def read_institution(institution_id: int, db: Session = Depends(get_db)):
    institution = get_institution_by_id(db, institution_id)

    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found"
        )

    return institution

@router.get(
    "/{institution_id}/departments",
    response_model=list[DepartmentRead]
)
def read_institution_departments(
    institution_id: int,
    db: Session = Depends(get_db)
):
    institution = get_institution_by_id(
        db,
        institution_id
    )

    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found"
        )

    return get_departments_by_institution(
        db,
        institution_id
    )