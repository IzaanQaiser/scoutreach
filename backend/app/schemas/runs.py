"""Request schemas for run endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RunCreateRequest(BaseModel):
    selected_batches: list[str] = Field(min_length=1, max_length=50)


FounderSelectionStrategy = Literal[
    "first_verified_email",
    "all_verified_founders",
    "manual_selected_founders",
]


class GenerateMessagesRequest(BaseModel):
    founder_selection_strategy: FounderSelectionStrategy = "first_verified_email"
    max_messages: int = Field(default=25, ge=1, le=100)
