from sqlalchemy.orm import Session

from app.departments.models import Department
from app.departments.schemas import DepartmentCreate

from app.institutions.models import Institution


def create_department(db: Session, department_data: DepartmentCreate):
    department = Department(**department_data.model_dump())

    db.add(department)
    db.commit()
    db.refresh(department)

    return department


def get_departments(db: Session):
    return db.query(Department).order_by(Department.name_el).all()


def get_department_by_id(db: Session, department_id: int):
    return db.query(Department).filter(Department.id == department_id).first()


def get_departments_by_institution(db: Session, institution_id: int):
    return (
        db.query(Department)
        .filter(Department.institution_id == institution_id)
        .order_by(Department.name_el)
        .all()
    )
    
def institution_exists(
    db: Session,
    institution_id: int
):
    return (
        db.query(Institution)
        .filter(Institution.id == institution_id)
        .first()
    )    