from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, JSON, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ProfileArtifact(Base):
    __tablename__ = "profile_artifacts"
    __table_args__ = (
        CheckConstraint(
            "type IN ('resume', 'github', 'website', 'devpost', 'manual')",
            name="ck_profile_artifacts_type",
        ),
        UniqueConstraint(
            "type",
            "content_hash",
            name="uq_profile_artifacts_type_content_hash",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String)
    source_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
