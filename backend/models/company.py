from datetime import datetime

from sqlalchemy import DateTime, Index, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_domain", "domain"),
        Index("ix_companies_normalized_name", "normalized_name"),
        Index(
            "ux_companies_source_external_id",
            "source",
            "source_external_id",
            unique=True,
            postgresql_where=text("source_external_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str | None] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    source_external_id: Mapped[str | None] = mapped_column(String)
    source_metadata: Mapped[dict[str, object]] = mapped_column(
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
