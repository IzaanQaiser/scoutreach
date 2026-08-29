from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class OutreachSend(Base):
    __tablename__ = "outreach_sends"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_outreach_sends_idempotency_key"),
        Index("ix_outreach_sends_draft_id", "draft_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(
        ForeignKey("outreach_drafts.id"),
        nullable=False,
    )
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    gmail_message_id: Mapped[str | None] = mapped_column(String)
    gmail_thread_id: Mapped[str | None] = mapped_column(String)
    provider_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )
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
