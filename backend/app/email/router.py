from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth.permissions import require_roles
from app.email.service import send_email
from app.users.models import User


router = APIRouter(
    prefix="/email",
    tags=["Email"],
)


@router.post(
    "/test",
    status_code=status.HTTP_200_OK,
)
def send_test_email(
    recipient: str,
    current_admin: User = Depends(
        require_roles(
            "SUPER_ADMIN",
            "INSTITUTION_ADMIN",
        )
    ),
):
    success = send_email(
        recipient=recipient,
        subject="Academic Platform - Test Email",
        body=(
            "This is a test email from "
            "the Academic Platform backend."
        ),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email sending failed",
        )

    return {
        "message": "Test email sent successfully"
    }