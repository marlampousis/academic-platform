from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.position_statuses.schemas import (
    PositionStatusCreate,
    PositionStatusRead,
    PositionStatusUpdate,
)

from app.position_statuses.service import (
    create_position_status,
    delete_position_status,
    get_all_position_statuses,
    get_position_status_by_code,
    get_position_status_by_id,
    update_position_status,
)


router = APIRouter(
    prefix="/position-statuses",
    tags=["Position Statuses"],
)


@router.get(
    "/",
    response_model=list[PositionStatusRead],
)
def read_position_statuses(
    db: Session = Depends(get_db),
):
    return get_all_position_statuses(db)


@router.get(
    "/code/{code}",
    response_model=PositionStatusRead,
)
def read_position_status_by_code(
    code: str,
    db: Session = Depends(get_db),
):
    position_status = get_position_status_by_code(
        db,
        code,
    )

    if not position_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position status not found",
        )

    return position_status


@router.get(
    "/{position_status_id}",
    response_model=PositionStatusRead,
)
def read_position_status(
    position_status_id: int,
    db: Session = Depends(get_db),
):
    position_status = get_position_status_by_id(
        db,
        position_status_id,
    )

    if not position_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position status not found",
        )

    return position_status


@router.post(
    "/",
    response_model=PositionStatusRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_position_status(
    position_status_data: PositionStatusCreate,
    db: Session = Depends(get_db),
):
    existing_status = get_position_status_by_code(
        db,
        position_status_data.code,
    )

    if existing_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position status code already exists",
        )

    return create_position_status(
        db,
        position_status_data,
    )


@router.put(
    "/{position_status_id}",
    response_model=PositionStatusRead,
)
def edit_position_status(
    position_status_id: int,
    position_status_data: PositionStatusUpdate,
    db: Session = Depends(get_db),
):
    position_status = get_position_status_by_id(
        db,
        position_status_id,
    )

    if not position_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position status not found",
        )

    return update_position_status(
        db,
        position_status,
        position_status_data,
    )


@router.delete(
    "/{position_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_position_status(
    position_status_id: int,
    db: Session = Depends(get_db),
):
    position_status = get_position_status_by_id(
        db,
        position_status_id,
    )

    if not position_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position status not found",
        )

    delete_position_status(
        db,
        position_status,
    )