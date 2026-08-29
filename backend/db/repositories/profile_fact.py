from sqlalchemy.orm import Session

from backend.models.profile_fact import ProfileFact


def create_profile_fact(
    session: Session,
    *,
    artifact_id: int,
    category: str,
    claim: str,
    evidence_text: str,
    importance: float | None = None,
) -> ProfileFact:
    fact = ProfileFact(
        artifact_id=artifact_id,
        category=category,
        claim=claim,
        evidence_text=evidence_text,
        importance=importance,
    )
    session.add(fact)
    session.flush()
    return fact


def get_profile_fact(session: Session, fact_id: int) -> ProfileFact | None:
    return session.get(ProfileFact, fact_id)
