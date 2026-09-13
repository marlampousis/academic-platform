def application_submitted_email(
    application_id: int,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Application Submitted"
    )

    body = (
        f"Your application #{application_id} "
        "was successfully submitted.\n\n"
        "You will be notified when its status changes."
    )

    return subject, body


def application_status_changed_email(
    application_id: int,
    new_status: str,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Application Status Updated"
    )

    body = (
        f"The status of your application "
        f"#{application_id} has changed to "
        f"{new_status}."
    )

    return subject, body


def missing_documents_email(
    application_id: int,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Missing Documents"
    )

    body = (
        f"Application #{application_id} "
        "is missing one or more required documents."
    )

    return subject, body


def application_assigned_email(
    application_id: int,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Application Assigned"
    )

    body = (
        f"Application #{application_id} "
        "has been assigned to your evaluation committee."
    )

    return subject, body


def evaluation_started_email(
    application_id: int,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Evaluation Started"
    )

    body = (
        f"The evaluation of application "
        f"#{application_id} has started."
    )

    return subject, body


def evaluation_completed_email(
    application_id: int,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Evaluation Completed"
    )

    body = (
        f"The evaluation of application "
        f"#{application_id} has been completed."
    )

    return subject, body


def final_decision_email(
    application_id: int,
    decision: str,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Final Decision"
    )

    body = (
        f"A final decision has been recorded "
        f"for application #{application_id}: "
        f"{decision}."
    )

    return subject, body


def deadline_reminder_email(
    position_id: int,
    days_remaining: int,
) -> tuple[str, str]:
    subject = (
        "Academic Platform - Application Deadline Reminder"
    )

    body = (
        f"The deadline for position "
        f"#{position_id} is in "
        f"{days_remaining} day(s)."
    )

    return subject, body