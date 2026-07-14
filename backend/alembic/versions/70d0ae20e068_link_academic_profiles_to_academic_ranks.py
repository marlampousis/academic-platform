"""link academic profiles to academic ranks

Revision ID: 70d0ae20e068
Revises: 7f7d1792e938
Create Date: 2026-07-14 01:27:18.609794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70d0ae20e068'
down_revision: Union[str, Sequence[str], None] = '7f7d1792e938'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "academic_profiles",
        sa.Column(
            "academic_rank_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_academic_profiles_academic_rank_id",
        "academic_profiles",
        "academic_ranks",
        ["academic_rank_id"],
        ["id"],
    )

    op.execute("""
        UPDATE academic_profiles ap
        SET academic_rank_id = ar.id
        FROM academic_ranks ar
        WHERE LOWER(TRIM(ap.academic_rank))
            = LOWER(TRIM(ar.name))
    """)

    op.drop_column(
        "academic_profiles",
        "academic_rank",
    )


def downgrade() -> None:
    op.add_column(
        "academic_profiles",
        sa.Column(
            "academic_rank",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.execute("""
        UPDATE academic_profiles ap
        SET academic_rank = ar.name
        FROM academic_ranks ar
        WHERE ap.academic_rank_id = ar.id
    """)

    op.drop_constraint(
        "fk_academic_profiles_academic_rank_id",
        "academic_profiles",
        type_="foreignkey",
    )

    op.drop_column(
        "academic_profiles",
        "academic_rank_id",
    )
