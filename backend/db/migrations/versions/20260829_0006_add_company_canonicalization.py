"""add company canonicalization

Revision ID: 20260829_0006
Revises: 20260829_0005
Create Date: 2026-08-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260829_0006"
down_revision: str | None = "20260829_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("canonical_company_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_companies_canonical_company_id_companies",
        "companies",
        "companies",
        ["canonical_company_id"],
        ["id"],
    )
    op.create_index(
        "ix_companies_canonical_company_id",
        "companies",
        ["canonical_company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_companies_canonical_company_id", table_name="companies")
    op.drop_constraint(
        "fk_companies_canonical_company_id_companies",
        "companies",
        type_="foreignkey",
    )
    op.drop_column("companies", "canonical_company_id")
