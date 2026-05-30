"""Schemas for auth/account/onboarding endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OnboardingStatus = Literal[
    "not_started",
    "in_progress",
    "completed",
    "completed_after_cap",
    "skipped_calibration",
]

OnboardingStep = Literal[
    "auth",
    "name",
    "profile_sources",
    "targets",
    "message_preferences",
    "calibration",
    "done",
]


class MeUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)


class CandidateProfileUpsertRequest(BaseModel):
    resume: str | None = None
    skills: dict = Field(default_factory=dict)
    github_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    bio: str | None = None
    extra_context: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    job_preferences: dict = Field(default_factory=dict)


class SettingsUpdateRequest(BaseModel):
    auto_send_enabled: bool | None = None
    message_preferences: dict | None = None


class OnboardingGenerateExamplesRequest(BaseModel):
    loop_index: int = Field(default=0, ge=0, le=3)


class RejectedExampleFeedback(BaseModel):
    example_id: str | None = None
    position_industry_feedback: str | None = None
    subject_feedback: str | None = None
    body_feedback: str | None = None


class OnboardingExampleFeedbackRequest(BaseModel):
    loop_index: int = Field(default=0, ge=0, le=3)
    rejected_examples: list[RejectedExampleFeedback] = Field(default_factory=list)


class OnboardingCompleteRequest(BaseModel):
    completion_mode: Literal["completed", "completed_after_cap", "skipped_calibration"] = "completed"
