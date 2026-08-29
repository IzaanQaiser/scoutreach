from sqlalchemy.orm import Session

from backend.models.outreach_draft import OutreachDraft


def create_outreach_draft(
    session: Session,
    *,
    contact_id: int,
    status: str,
    subject: str | None = None,
    body: str | None = None,
    research_snapshot: dict[str, object] | None = None,
    profile_fact_ids: list[int] | None = None,
    model_metadata: dict[str, object] | None = None,
) -> OutreachDraft:
    draft = OutreachDraft(
        contact_id=contact_id,
        status=status,
        subject=subject,
        body=body,
        research_snapshot=research_snapshot or {},
        profile_fact_ids=profile_fact_ids or [],
        model_metadata=model_metadata or {},
    )
    session.add(draft)
    session.flush()
    return draft


def get_outreach_draft(session: Session, draft_id: int) -> OutreachDraft | None:
    return session.get(OutreachDraft, draft_id)
