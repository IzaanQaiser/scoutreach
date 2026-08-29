from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.outreach_send import OutreachSend


def create_outreach_send(
    session: Session,
    *,
    draft_id: int,
    recipient: str,
    subject: str,
    body: str,
    sent_at: datetime,
    provider: str,
    idempotency_key: str,
    gmail_message_id: str | None = None,
    gmail_thread_id: str | None = None,
    provider_metadata: dict[str, object] | None = None,
    research_snapshot: dict[str, object] | None = None,
    profile_fact_ids: list[int] | None = None,
) -> OutreachSend:
    send = OutreachSend(
        draft_id=draft_id,
        recipient=recipient,
        subject=subject,
        body=body,
        sent_at=sent_at,
        provider=provider,
        idempotency_key=idempotency_key,
        gmail_message_id=gmail_message_id,
        gmail_thread_id=gmail_thread_id,
        provider_metadata=provider_metadata or {},
        research_snapshot=research_snapshot or {},
        profile_fact_ids=profile_fact_ids or [],
    )
    session.add(send)
    session.flush()
    return send


def get_outreach_send(session: Session, send_id: int) -> OutreachSend | None:
    return session.get(OutreachSend, send_id)
