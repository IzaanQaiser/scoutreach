from sqlalchemy.orm import Session

from backend.models.contact import Contact


def create_contact(
    session: Session,
    *,
    company_id: int,
    name: str,
    source: str,
    title: str | None = None,
    role_category: str | None = None,
    linkedin_url: str | None = None,
    source_confidence: float | None = None,
) -> Contact:
    contact = Contact(
        company_id=company_id,
        name=name,
        source=source,
        title=title,
        role_category=role_category,
        linkedin_url=linkedin_url,
        source_confidence=source_confidence,
    )
    session.add(contact)
    session.flush()
    return contact


def get_contact(session: Session, contact_id: int) -> Contact | None:
    return session.get(Contact, contact_id)
