from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.users.models import User
from app.users.router import get_current_user


def require_roles(
    *allowed_role_codes: str,
) -> Callable:
    normalized_roles = {
        code.strip().upper()
        for code in allowed_role_codes
    }

    def role_checker(
        current_user: User = Depends(
            get_current_user
        ),
    ) -> User:
        if (
            not current_user.role
            or current_user.role.code
            not in normalized_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker

from sqlalchemy.orm import Session
from app.committee_members.models import CommitteeMember


def require_committee_access(
    db: Session,
    committee_id: int,
    current_user: User,
) -> None:

    role_code = (
        current_user.role.code
        if current_user.role
        else None
    )

    # Global administrators have access.
    # Institution admins are restricted until
    # institution-level authorization exists.
    if role_code == "SUPER_ADMIN":
        return

    if role_code != "REVIEWER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    membership = (
        db.query(CommitteeMember)
        .filter(
            CommitteeMember.committee_id == committee_id,
            CommitteeMember.user_id == current_user.id,
            CommitteeMember.is_active.is_(True),
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this committee",
        )