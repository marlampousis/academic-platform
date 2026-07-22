"""add roles lookup table

Revision ID: 679de73a7297
Revises: 9eb22a406f41
Create Date: 2026-07-20 21:22:13.023437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '679de73a7297'
down_revision: Union[str, Sequence[str], None] = '9eb22a406f41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_index(
        op.f("ix_roles_id"),
        "roles",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_roles_code"),
        "roles",
        ["code"],
        unique=True,
    )

    roles_table = sa.table(
        "roles",
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )

    op.bulk_insert(
        roles_table,
        [
            {
                "code": "SUPER_ADMIN",
                "name": "Super Administrator",
                "description": (
                    "Manages the entire platform "
                    "and all institutions."
                ),
            },
            {
                "code": "INSTITUTION_ADMIN",
                "name": "Institution Administrator",
                "description": (
                    "Manages positions and applications "
                    "for an institution."
                ),
            },
            {
                "code": "REVIEWER",
                "name": "Reviewer",
                "description": (
                    "Reviews applications assigned "
                    "to an evaluation committee."
                ),
            },
            {
                "code": "CANDIDATE",
                "name": "Candidate",
                "description": (
                    "Maintains an academic profile "
                    "and submits applications."
                ),
            },
        ],
    )

    op.add_column(
        "users",
        sa.Column(
            "role_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET role_id = roles.id
        FROM roles
        WHERE UPPER(users.role) = roles.code
        """
    )

    op.execute(
        """
        UPDATE users
        SET role_id = (
            SELECT id
            FROM roles
            WHERE code = 'CANDIDATE'
        )
        WHERE role_id IS NULL
        """
    )

    op.alter_column(
        "users",
        "role_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_index(
        op.f("ix_users_role_id"),
        "users",
        ["role_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_users_role_id_roles",
        "users",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_column(
        "users",
        "role",
    )


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET role = roles.code
        FROM roles
        WHERE users.role_id = roles.id
        """
    )

    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    op.drop_constraint(
        "fk_users_role_id_roles",
        "users",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_users_role_id"),
        table_name="users",
    )

    op.drop_column(
        "users",
        "role_id",
    )

    op.drop_index(
        op.f("ix_roles_code"),
        table_name="roles",
    )

    op.drop_index(
        op.f("ix_roles_id"),
        table_name="roles",
    )

    op.drop_table(
        "roles",
    )
