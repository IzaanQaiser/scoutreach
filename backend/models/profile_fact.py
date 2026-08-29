from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ProfileFact(Base):
    __tablename__ = "profile_facts"
    __table_args__ = (Index("ix_profile_facts_artifact_id", "artifact_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    artifact_id: Mapped[int] = mapped_column(
        ForeignKey("profile_artifacts.id"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
