"""Schemas for company review endpoints (Phase 4)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


CompanyReviewStatus = Literal["pending_review", "accepted", "rejected"]
CompanyFilterStatus = Literal[
    "pending_review",
    "accepted",
    "rejected",
    "dossier_failed",
    "scrape_failed",
    "email_lookup_failed",
]


class CompanyStatusUpdateRequest(BaseModel):
    status: CompanyReviewStatus
