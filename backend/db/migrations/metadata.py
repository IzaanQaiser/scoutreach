from backend.db.base import Base
from backend.models import (
    Company,
    Contact,
    ContactMethod,
    Job,
    JobPosting,
    OutreachDraft,
    OutreachSend,
    ProfileArtifact,
    ProfileFact,
)


target_metadata = Base.metadata

__all__ = [
    "Company",
    "Contact",
    "ContactMethod",
    "Job",
    "JobPosting",
    "OutreachDraft",
    "OutreachSend",
    "ProfileArtifact",
    "ProfileFact",
    "target_metadata",
]
