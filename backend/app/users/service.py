from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.users.models import User
from app.roles.service import get_role_by_code
from app.users.schemas import UserCreate
from app.core.security import hash_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    user_data: UserCreate,
):
    candidate_role = get_role_by_code(
        db,
        "CANDIDATE",
    )

    if not candidate_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Default candidate role "
                "is not configured"
            ),
        )

    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        hashed_password=hash_password(
            user_data.password
        ),
        role_id=candidate_role.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user