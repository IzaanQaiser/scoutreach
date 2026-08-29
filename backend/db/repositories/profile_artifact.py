from sqlalchemy.orm import Session

from backend.models.profile_artifact import ProfileArtifact


def create_profile_artifact(
    session: Session,
    *,
    type: str,
    content_text: str,
    content_hash: str,
    url: str | None = None,
    source_metadata: dict[str, object] | None = None,
) -> ProfileArtifact:
    artifact = ProfileArtifact(
        type=type,
        content_text=content_text,
        content_hash=content_hash,
        url=url,
        source_metadata=source_metadata or {},
    )
    session.add(artifact)
    session.flush()
    return artifact


def get_profile_artifact(
    session: Session,
    artifact_id: int,
) -> ProfileArtifact | None:
    return session.get(ProfileArtifact, artifact_id)
