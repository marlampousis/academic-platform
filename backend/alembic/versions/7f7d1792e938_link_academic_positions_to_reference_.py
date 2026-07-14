"""link academic positions to reference tables

Revision ID: 7f7d1792e938
Revises: 852ad91cfe95
Create Date: 2026-07-13 07:39:17.403275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f7d1792e938'
down_revision: Union[str, Sequence[str], None] = '852ad91cfe95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "academic_positions",
        sa.Column(
            "academic_rank_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "academic_positions",
        sa.Column(
            "employment_type_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "academic_positions",
        sa.Column(
            "position_status_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_academic_positions_academic_rank_id",
        "academic_positions",
        "academic_ranks",
        ["academic_rank_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_academic_positions_employment_type_id",
        "academic_positions",
        "employment_types",
        ["employment_type_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_academic_positions_position_status_id",
        "academic_positions",
        "position_statuses",
        ["position_status_id"],
        ["id"],
    )

    op.execute("""
        UPDATE academic_positions ap
        SET academic_rank_id = ar.id
        FROM academic_ranks ar
        WHERE LOWER(TRIM(ap.academic_rank))
            = LOWER(TRIM(ar.name))
    """)

    op.execute("""
        UPDATE academic_positions ap
        SET employment_type_id = et.id
        FROM employment_types et
        WHERE LOWER(TRIM(ap.employment_type))
            = LOWER(TRIM(et.name))
    """)

    op.execute("""
        UPDATE academic_positions ap
        SET position_status_id = ps.id
        FROM position_statuses ps
        WHERE LOWER(TRIM(ap.status))
            = LOWER(TRIM(ps.code))
           OR LOWER(TRIM(ap.status))
            = LOWER(TRIM(ps.name))
    """)

    op.alter_column(
        "academic_positions",
        "academic_rank_id",
        nullable=False,
    )

    op.alter_column(
        "academic_positions",
        "employment_type_id",
        nullable=False,
    )

    op.alter_column(
        "academic_positions",
        "position_status_id",
        nullable=False,
    )

    op.drop_column(
        "academic_positions",
        "academic_rank",
    )

    op.drop_column(
        "academic_positions",
        "employment_type",
    )

    op.drop_column(
        "academic_positions",
        "status",
    )


def downgrade() -> None:
    op.add_column(
        "academic_positions",
        sa.Column(
            "academic_rank",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "academic_positions",
        sa.Column(
            "employment_type",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "academic_positions",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.execute("""
        UPDATE academic_positions ap
        SET academic_rank = ar.name
        FROM academic_ranks ar
        WHERE ap.academic_rank_id = ar.id
    """)

    op.execute("""
        UPDATE academic_positions ap
        SET employment_type = et.name
        FROM employment_types et
        WHERE ap.employment_type_id = et.id
    """)

    op.execute("""
        UPDATE academic_positions ap
        SET status = ps.code
        FROM position_statuses ps
        WHERE ap.position_status_id = ps.id
    """)

    op.alter_column(
        "academic_positions",
        "academic_rank",
        nullable=False,
    )

    op.alter_column(
        "academic_positions",
        "employment_type",
        nullable=False,
    )

    op.alter_column(
        "academic_positions",
        "status",
        nullable=False,
    )

    op.drop_constraint(
        "fk_academic_positions_academic_rank_id",
        "academic_positions",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_academic_positions_employment_type_id",
        "academic_positions",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_academic_positions_position_status_id",
        "academic_positions",
        type_="foreignkey",
    )

    op.drop_column(
        "academic_positions",
        "academic_rank_id",
    )

    op.drop_column(
        "academic_positions",
        "employment_type_id",
    )

    op.drop_column(
        "academic_positions",
        "position_status_id",
    )
