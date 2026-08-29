from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (
        Index("ix_job_postings_company_id", "company_id"),
        Index("ix_job_postings_active", "active"),
        Index(
            "ux_job_postings_source_external_id",
            "source",
            "external_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    function: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    raw_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )
    seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
