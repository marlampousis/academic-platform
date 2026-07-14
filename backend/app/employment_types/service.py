from sqlalchemy.orm import Session

from app.employment_types.models import EmploymentType
from app.employment_types.schemas import (
    EmploymentTypeCreate,
    EmploymentTypeUpdate,
)


def get_all_employment_types(db: Session):
    return (
        db.query(EmploymentType)
        .order_by(EmploymentType.name.asc())
        .all()
    )


def get_employment_type_by_id(
    db: Session,
    employment_type_id: int,
):
    return (
        db.query(EmploymentType)
        .filter(EmploymentType.id == employment_type_id)
        .first()
    )


def get_employment_type_by_code(
    db: Session,
    code: str,
):
    return (
        db.query(EmploymentType)
        .filter(EmploymentType.code == code)
        .first()
    )


def create_employment_type(
    db: Session,
    employment_type_data: EmploymentTypeCreate,
):
    employment_type = EmploymentType(
        **employment_type_data.model_dump()
    )

    db.add(employment_type)
    db.commit()
    db.refresh(employment_type)

    return employment_type


def update_employment_type(
    db: Session,
    employment_type: EmploymentType,
    employment_type_data: EmploymentTypeUpdate,
):
    update_data = employment_type_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(employment_type, field, value)

    db.commit()
    db.refresh(employment_type)

    return employment_type


def delete_employment_type(
    db: Session,
    employment_type: EmploymentType,
):
    db.delete(employment_type)
    db.commit()