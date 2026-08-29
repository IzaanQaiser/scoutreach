from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'READY', 'SAVED', 'REJECTED', 'SENT')",
            name="ck_outreach_drafts_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    research_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )
    profile_fact_ids: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default=text("'[]'::json"),
    )
    model_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
