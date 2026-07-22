from sqlalchemy.orm import Session

from app.roles.models import Role


DEFAULT_ROLES = [
    {
        "code": "SUPER_ADMIN",
        "name": "Super Administrator",
        "description": (
            "Manages the entire platform and all institutions."
        ),
    },
    {
        "code": "INSTITUTION_ADMIN",
        "name": "Institution Administrator",
        "description": (
            "Manages academic positions and applications "
            "for a specific institution."
        ),
    },
    {
        "code": "REVIEWER",
        "name": "Reviewer",
        "description": (
            "Reviews applications assigned to an "
            "evaluation committee."
        ),
    },
    {
        "code": "CANDIDATE",
        "name": "Candidate",
        "description": (
            "Maintains an academic profile and "
            "submits applications."
        ),
    },
]


def seed_roles(db: Session) -> None:
    for role_data in DEFAULT_ROLES:
        existing_role = (
            db.query(Role)
            .filter(Role.code == role_data["code"])
            .first()
        )

        if existing_role:
            existing_role.name = role_data["name"]
            existing_role.description = (
                role_data["description"]
            )
        else:
            db.add(Role(**role_data))

    db.commit()