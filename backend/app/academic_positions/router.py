from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.users.models import User
from app.users.router import get_current_user

from app.academic_positions.schemas import (
    AcademicPositionCreate,
    AcademicPositionRead,
    AcademicPositionUpdate,
)

from app.academic_positions.service import (
    create_position,
    get_positions,
    get_position_by_id,
    update_position,
    delete_position,
)
from app.institutions.models import Institution
from app.departments.models import Department

router = APIRouter(
    prefix="/positions",
    tags=["Academic Positions"],
)


@router.post(
    "/",
    response_model=AcademicPositionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_position(
    position_data: AcademicPositionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    institution = (
        db.query(Institution)
        .filter(Institution.id == position_data.institution_id)
        .first()
    )

    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    department = (
        db.query(Department)
        .filter(Department.id == position_data.department_id)
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    if department.institution_id != institution.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department does not belong to the selected institution",
        )

    return create_position(
        db=db,
        user_id=current_user.id,
        position_data=position_data,
    )

@router.get(
    "/",
    response_model=list[AcademicPositionRead],
)
def read_positions(
    db: Session = Depends(get_db),
):
    return get_positions(db)


@router.get(
    "/{position_id}",
    response_model=AcademicPositionRead,
)
def read_position(
    position_id: int,
    db: Session = Depends(get_db),
):
    position = get_position_by_id(db, position_id)

    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found",
        )

    return position


@router.put(
    "/{position_id}",
    response_model=AcademicPositionRead,
)
def edit_position(
    position_id: int,
    position_data: AcademicPositionUpdate,
    db: Session = Depends(get_db),
):
    position = get_position_by_id(db, position_id)

    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found",
        )

    return update_position(
        db,
        position,
        position_data,
    )


@router.delete(
    "/{position_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_position(
    position_id: int,
    db: Session = Depends(get_db),
):
    position = get_position_by_id(db, position_id)

    if not position:
        raise HTTPException(
            status_code=404,
            detail="Position not found",
        )

    delete_position(
        db,
        position,
    )