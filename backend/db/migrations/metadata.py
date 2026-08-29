from backend.db.base import Base
from backend.models import Company, JobPosting


target_metadata = Base.metadata

__all__ = ["Company", "JobPosting", "target_metadata"]
