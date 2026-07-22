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