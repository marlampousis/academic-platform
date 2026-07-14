"""link documents to document types

Revision ID: 112a59f73217
Revises: 70d0ae20e068
Create Date: 2026-07-14 08:38:41.152649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '112a59f73217'
down_revision: Union[str, Sequence[str], None] = '70d0ae20e068'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "document_type_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_documents_document_type_id",
        "documents",
        "document_types",
        ["document_type_id"],
        ["id"],
    )

    op.execute("""
        UPDATE documents d
        SET document_type_id = dt.id
        FROM document_types dt
        WHERE LOWER(TRIM(d.document_type))
            = LOWER(TRIM(dt.code))
           OR LOWER(TRIM(d.document_type))
            = LOWER(TRIM(dt.name))
    """)

    op.alter_column(
        "documents",
        "document_type_id",
        nullable=False,
    )

    op.drop_column(
        "documents",
        "document_type",
    )


def downgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "document_type",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.execute("""
        UPDATE documents d
        SET document_type = dt.code
        FROM document_types dt
        WHERE d.document_type_id = dt.id
    """)

    op.alter_column(
        "documents",
        "document_type",
        nullable=False,
    )

    op.drop_constraint(
        "fk_documents_document_type_id",
        "documents",
        type_="foreignkey",
    )

    op.drop_column(
        "documents",
        "document_type_id",
    )
