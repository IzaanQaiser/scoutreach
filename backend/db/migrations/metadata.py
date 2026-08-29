from backend.db.base import Base
from backend.models import Company, Contact, ContactMethod, JobPosting


target_metadata = Base.metadata

__all__ = ["Company", "Contact", "ContactMethod", "JobPosting", "target_metadata"]
