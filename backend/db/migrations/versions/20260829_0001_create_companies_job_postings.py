"""create companies and job postings

Revision ID: 20260829_0001
Revises:
Create Date: 2026-08-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260829_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("normalized_name", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("source_external_id", sa.String(), nullable=True),
        sa.Column(
            "source_metadata",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_domain", "companies", ["domain"])
    op.create_index(
        "ix_companies_normalized_name",
        "companies",
        ["normalized_name"],
    )
    op.create_index(
        "ux_companies_source_external_id",
        "companies",
        ["source", "source_external_id"],
        unique=True,
        postgresql_where=sa.text("source_external_id IS NOT NULL"),
    )

    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("function", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "raw_metadata",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_postings_active", "job_postings", ["active"])
    op.create_index(
        "ix_job_postings_company_id",
        "job_postings",
        ["company_id"],
    )
    op.create_index(
        "ux_job_postings_source_external_id",
        "job_postings",
        ["source", "external_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_job_postings_source_external_id",
        table_name="job_postings",
    )
    op.drop_index("ix_job_postings_company_id", table_name="job_postings")
    op.drop_index("ix_job_postings_active", table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_index("ux_companies_source_external_id", table_name="companies")
    op.drop_index("ix_companies_normalized_name", table_name="companies")
    op.drop_index("ix_companies_domain", table_name="companies")
    op.drop_table("companies")
