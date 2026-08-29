from sqlalchemy.orm import Session

from backend.models.contact_method import ContactMethod


def create_contact_method(
    session: Session,
    *,
    contact_id: int,
    type: str,
    value: str,
    source: str,
    verification_status: str | None = None,
    confidence: float | None = None,
    is_primary: bool = False,
) -> ContactMethod:
    contact_method = ContactMethod(
        contact_id=contact_id,
        type=type,
        value=value,
        source=source,
        verification_status=verification_status,
        confidence=confidence,
        is_primary=is_primary,
    )
    session.add(contact_method)
    session.flush()
    return contact_method


def get_contact_method(
    session: Session,
    contact_method_id: int,
) -> ContactMethod | None:
    return session.get(ContactMethod, contact_method_id)
