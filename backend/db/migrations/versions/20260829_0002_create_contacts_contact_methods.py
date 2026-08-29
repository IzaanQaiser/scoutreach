"""create contacts and contact methods

Revision ID: 20260829_0002
Revises: 20260829_0001
Create Date: 2026-08-29
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260829_0002"
down_revision: str | None = "20260829_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("role_category", sa.String(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("source_confidence", sa.Float(), nullable=True),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])

    op.create_table(
        "contact_methods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("verification_status", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "contact_id",
            "type",
            "value",
            name="uq_contact_methods_contact_type_value",
        ),
    )
    op.create_index(
        "ix_contact_methods_contact_id",
        "contact_methods",
        ["contact_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_contact_methods_contact_id", table_name="contact_methods")
    op.drop_table("contact_methods")
    op.drop_index("ix_contacts_company_id", table_name="contacts")
    op.drop_table("contacts")
