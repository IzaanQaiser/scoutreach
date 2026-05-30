"""Schemas for outreach review/regenerate/send endpoints (Phase 6)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OutreachFilterStatus = Literal[
    "draft",
    "approved",
    "needs_review",
    "rejected",
    "generation_failed",
    "sending",
    "sent",
    "failed",
]

OutreachEditableStatus = Literal[
    "draft",
    "approved",
    "needs_review",
    "rejected",
]


class OutreachUpdateRequest(BaseModel):
    subject: str | None = None
    message_content: str | None = None
    status: OutreachEditableStatus | None = None
    review_notes: str | None = None


class OutreachRegenerateRequest(BaseModel):
    critique: str = Field(min_length=1, max_length=2000)
    message_preferences_override: dict | None = None


class SendApprovedRequest(BaseModel):
    send_mode: Literal["approved_only"] = "approved_only"


class SendSingleRequest(BaseModel):
    confirm_send: bool
