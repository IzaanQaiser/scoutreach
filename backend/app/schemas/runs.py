"""Request schemas for run endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunCreateRequest(BaseModel):
    selected_batches: list[str] = Field(min_length=1, max_length=50)

