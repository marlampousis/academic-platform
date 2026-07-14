from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.employment_types.schemas import (
    EmploymentTypeCreate,
    EmploymentTypeRead,
    EmploymentTypeUpdate,
)

from app.employment_types.service import (
    create_employment_type,
    delete_employment_type,
    get_all_employment_types,
    get_employment_type_by_code,
    get_employment_type_by_id,
    update_employment_type,
)


router = APIRouter(
    prefix="/employment-types",
    tags=["Employment Types"],
)


@router.get(
    "/",
    response_model=list[EmploymentTypeRead],
)
def read_employment_types(
    db: Session = Depends(get_db),
):
    return get_all_employment_types(db)


@router.get(
    "/code/{code}",
    response_model=EmploymentTypeRead,
)
def read_employment_type_by_code(
    code: str,
    db: Session = Depends(get_db),
):
    employment_type = get_employment_type_by_code(
        db,
        code,
    )

    if not employment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment type not found",
        )

    return employment_type


@router.get(
    "/{employment_type_id}",
    response_model=EmploymentTypeRead,
)
def read_employment_type(
    employment_type_id: int,
    db: Session = Depends(get_db),
):
    employment_type = get_employment_type_by_id(
        db,
        employment_type_id,
    )

    if not employment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment type not found",
        )

    return employment_type


@router.post(
    "/",
    response_model=EmploymentTypeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_employment_type(
    employment_type_data: EmploymentTypeCreate,
    db: Session = Depends(get_db),
):
    existing_code = get_employment_type_by_code(
        db,
        employment_type_data.code,
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employment type code already exists",
        )

    return create_employment_type(
        db,
        employment_type_data,
    )


@router.put(
    "/{employment_type_id}",
    response_model=EmploymentTypeRead,
)
def edit_employment_type(
    employment_type_id: int,
    employment_type_data: EmploymentTypeUpdate,
    db: Session = Depends(get_db),
):
    employment_type = get_employment_type_by_id(
        db,
        employment_type_id,
    )

    if not employment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment type not found",
        )

    return update_employment_type(
        db,
        employment_type,
        employment_type_data,
    )


@router.delete(
    "/{employment_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_employment_type(
    employment_type_id: int,
    db: Session = Depends(get_db),
):
    employment_type = get_employment_type_by_id(
        db,
        employment_type_id,
    )

    if not employment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment type not found",
        )

    delete_employment_type(
        db,
        employment_type,
    )