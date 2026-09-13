import smtplib

from email.message import EmailMessage

from app.core.config import settings


def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    if not settings.EMAIL_ENABLED:
        return False

    if not settings.EMAIL_USERNAME:
        raise ValueError(
            "EMAIL_USERNAME is not configured"
        )

    if not settings.EMAIL_PASSWORD:
        raise ValueError(
            "EMAIL_PASSWORD is not configured"
        )

    sender_email = (
        settings.EMAIL_FROM
        or settings.EMAIL_USERNAME
    )

    message = EmailMessage()

    message["From"] = (
        f"{settings.EMAIL_FROM_NAME} "
        f"<{sender_email}>"
    )

    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    try:
        with smtplib.SMTP(
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
        ) as smtp:
            if settings.EMAIL_USE_TLS:
                smtp.starttls()

            smtp.login(
                settings.EMAIL_USERNAME,
                settings.EMAIL_PASSWORD,
            )

            smtp.send_message(message)

        return True

    except Exception as exc:
        print(
            f"Email sending failed: {exc}"
        )

        return False