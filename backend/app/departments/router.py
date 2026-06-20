from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.departments.service import institution_exists

from app.core.database import get_db
from app.departments.schemas import DepartmentCreate, DepartmentRead
from app.departments.service import (
    create_department,
    get_departments,
    get_department_by_id,
    get_departments_by_institution,
)


router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


@router.post(
    "/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED
)
def create_new_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db)
):

    institution = institution_exists(
        db,
        department_data.institution_id
    )

    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found"
        )

    return create_department(
        db,
        department_data
    )

@router.get("/", response_model=list[DepartmentRead])
def read_departments(db: Session = Depends(get_db)):
    return get_departments(db)


@router.get("/{department_id}", response_model=DepartmentRead)
def read_department(department_id: int, db: Session = Depends(get_db)):
    department = get_department_by_id(db, department_id)

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    return department


@router.get("/institution/{institution_id}", response_model=list[DepartmentRead])
def read_departments_by_institution(
    institution_id: int,
    db: Session = Depends(get_db)
):
    return get_departments_by_institution(db, institution_id)

