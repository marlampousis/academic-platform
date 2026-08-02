from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.permissions import require_roles
from app.committee_members.schemas import (
    CommitteeMemberCreate,
    CommitteeMemberRead,
    CommitteeMemberUpdate,
)
from app.committee_members.service import (
    create_committee_member,
    delete_committee_member,
    get_active_committee_chair,
    get_committee_member_by_id,
    get_committee_member_by_user,
    get_committee_members,
    update_committee_member,
)
from app.core.database import get_db
from app.evaluation_committees.service import (
    get_evaluation_committee_by_id,
)
from app.users.models import User


router = APIRouter(
    prefix="/evaluation-committees",
    tags=["Committee Members"],
)


ALLOWED_COMMITTEE_USER_ROLES = {
    "SUPER_ADMIN",
    "INSTITUTION_ADMIN",
    "REVIEWER",
}


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


@router.post(
    "/{committee_id}/members",
    response_model=CommitteeMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_committee_member(
    committee_id: int,
    member_data: CommitteeMemberCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    if committee.status not in {
        "DRAFT",
        "ACTIVE",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Members can only be added to "
                "draft or active committees"
            ),
        )

    user = get_user_by_id(
        db,
        member_data.user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if (
        not user.role
        or user.role.code
        not in ALLOWED_COMMITTEE_USER_ROLES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only reviewers or administrators "
                "can become committee members"
            ),
        )

    existing_member = get_committee_member_by_user(
        db=db,
        committee_id=committee_id,
        user_id=member_data.user_id,
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "User is already a member "
                "of this committee"
            ),
        )

    if member_data.role_in_committee == "CHAIR":
        existing_chair = get_active_committee_chair(
            db,
            committee_id,
        )

        if existing_chair:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This committee already has "
                    "an active chair"
                ),
            )

    return create_committee_member(
        db=db,
        committee_id=committee_id,
        member_data=member_data,
    )


@router.get(
    "/{committee_id}/members",
    response_model=list[CommitteeMemberRead],
)
def read_committee_members(
    committee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
            "REVIEWER",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    return get_committee_members(
        db=db,
        committee_id=committee_id,
    )


@router.get(
    "/{committee_id}/members/{member_id}",
    response_model=CommitteeMemberRead,
)
def read_committee_member(
    committee_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
            "REVIEWER",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    committee_member = (
        get_committee_member_by_id(
            db,
            member_id,
        )
    )

    if (
        not committee_member
        or committee_member.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee member not found",
        )

    return committee_member


@router.put(
    "/{committee_id}/members/{member_id}",
    response_model=CommitteeMemberRead,
)
def edit_committee_member(
    committee_id: int,
    member_id: int,
    member_data: CommitteeMemberUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    if committee.status not in {
        "DRAFT",
        "ACTIVE",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Members cannot be modified in "
                "completed or cancelled committees"
            ),
        )

    committee_member = (
        get_committee_member_by_id(
            db,
            member_id,
        )
    )

    if (
        not committee_member
        or committee_member.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee member not found",
        )

    resulting_role = (
        member_data.role_in_committee
        if member_data.role_in_committee is not None
        else committee_member.role_in_committee
    )

    resulting_active_status = (
        member_data.is_active
        if member_data.is_active is not None
        else committee_member.is_active
    )

    if (
        resulting_role == "CHAIR"
        and resulting_active_status
    ):
        existing_chair = get_active_committee_chair(
            db=db,
            committee_id=committee_id,
            excluded_member_id=committee_member.id,
        )

        if existing_chair:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This committee already has "
                    "an active chair"
                ),
            )

    return update_committee_member(
        db=db,
        committee_member=committee_member,
        member_data=member_data,
    )


@router.delete(
    "/{committee_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_committee_member(
    committee_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    committee = get_evaluation_committee_by_id(
        db,
        committee_id,
    )

    if not committee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation committee not found",
        )

    if committee.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Committee members can only be "
                "deleted while the committee is draft"
            ),
        )

    committee_member = (
        get_committee_member_by_id(
            db,
            member_id,
        )
    )

    if (
        not committee_member
        or committee_member.committee_id
        != committee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Committee member not found",
        )

    delete_committee_member(
        db=db,
        committee_member=committee_member,
    )