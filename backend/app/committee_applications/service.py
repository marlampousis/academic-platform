from sqlalchemy.orm import Session, joinedload

from app.committee_applications.models import (
    CommitteeApplication,
)
from app.committee_applications.schemas import (
    CommitteeApplicationCreate,
    CommitteeApplicationUpdate,
)

ALLOWED_ASSIGNMENT_TRANSITIONS = {
    "ASSIGNED": {
        "IN_EVALUATION",
        "CANCELLED",
    },
    "IN_EVALUATION": {
        "COMPLETED",
        "CANCELLED",
    },
}

def create_committee_application(
    db: Session,
    committee_id: int,
    assignment_data: CommitteeApplicationCreate,
    assigned_by: int,
) -> CommitteeApplication:
    assignment = CommitteeApplication(
        committee_id=committee_id,
        application_id=assignment_data.application_id,
        assigned_by=assigned_by,
        status="ASSIGNED",
        notes=assignment_data.notes,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return get_committee_application_by_id(
        db=db,
        assignment_id=assignment.id,
    )


def get_committee_applications(
    db: Session,
    committee_id: int,
) -> list[CommitteeApplication]:
    return (
        db.query(CommitteeApplication)
        .options(
            joinedload(
                CommitteeApplication.application
            )
        )
        .filter(
            CommitteeApplication.committee_id
            == committee_id
        )
        .order_by(
            CommitteeApplication.assigned_at.desc(),
            CommitteeApplication.id.desc(),
        )
        .all()
    )


def get_committee_application_by_id(
    db: Session,
    assignment_id: int,
) -> CommitteeApplication | None:
    return (
        db.query(CommitteeApplication)
        .options(
            joinedload(
                CommitteeApplication.application
            )
        )
        .filter(
            CommitteeApplication.id
            == assignment_id
        )
        .first()
    )


def get_assignment_by_application(
    db: Session,
    application_id: int,
) -> CommitteeApplication | None:
    return (
        db.query(CommitteeApplication)
        .filter(
            CommitteeApplication.application_id
            == application_id
        )
        .first()
    )


def update_committee_application(
    db: Session,
    assignment: CommitteeApplication,
    assignment_data: CommitteeApplicationUpdate,
) -> CommitteeApplication:
    update_data = assignment_data.model_dump(
        exclude_unset=True
    )

    new_status = update_data.get("status")

    if new_status is not None:
        normalized_status = (
            new_status.strip().upper()
        )

        if normalized_status != assignment.status:
            validate_assignment_status_transition(
                current_status=assignment.status,
                new_status=normalized_status,
            )

        update_data["status"] = normalized_status

    for field, value in update_data.items():
        setattr(
            assignment,
            field,
            value,
        )

    db.commit()
    db.refresh(assignment)

    return get_committee_application_by_id(
        db=db,
        assignment_id=assignment.id,
    )


def delete_committee_application(
    db: Session,
    assignment: CommitteeApplication,
) -> None:
    db.delete(assignment)
    db.commit()
    
def validate_assignment_status_transition(
    current_status: str,
    new_status: str,
) -> None:
    normalized_current = (
        current_status.strip().upper()
    )

    normalized_new = (
        new_status.strip().upper()
    )

    allowed_statuses = (
        ALLOWED_ASSIGNMENT_TRANSITIONS.get(
            normalized_current,
            set(),
        )
    )

    if normalized_new not in allowed_statuses:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid committee application "
                "status transition: "
                f"{normalized_current} -> "
                f"{normalized_new}"
            ),
        )    