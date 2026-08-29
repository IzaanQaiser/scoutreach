from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.job import Job


class JobStateError(RuntimeError):
    pass


class JobProgressError(ValueError):
    pass


def enqueue(
    session: Session,
    *,
    type: str,
    payload: dict[str, object] | None = None,
    progress_total: int | None = None,
) -> Job:
    if progress_total is not None and progress_total < 0:
        raise JobProgressError("progress_total must be non-negative")
    job = Job(
        type=type,
        payload=payload or {},
        status="PENDING",
        progress_current=0,
        progress_total=progress_total,
    )
    session.add(job)
    session.flush()
    return job


def get_job(session: Session, job_id: int) -> Job | None:
    return session.get(Job, job_id)


def claim_next(session: Session) -> Job | None:
    job = session.scalar(
        select(Job)
        .where(Job.status == "PENDING")
        .order_by(Job.created_at, Job.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None
    job.status = "RUNNING"
    job.started_at = datetime.now(timezone.utc)
    session.flush()
    return job


def set_progress(session: Session, job_id: int, progress_current: int) -> Job:
    job = _locked_job(session, job_id)
    _require_running(job)
    if progress_current < 0:
        raise JobProgressError("progress_current must be non-negative")
    if job.progress_total is not None and progress_current > job.progress_total:
        raise JobProgressError("progress_current cannot exceed progress_total")
    job.progress_current = progress_current
    session.flush()
    return job


def succeed(session: Session, job_id: int) -> Job:
    job = _locked_job(session, job_id)
    _require_running(job)
    job.status = "SUCCEEDED"
    job.error = None
    if job.progress_total is not None:
        job.progress_current = job.progress_total
    job.finished_at = datetime.now(timezone.utc)
    session.flush()
    return job


def fail(session: Session, job_id: int, error: str) -> Job:
    job = _locked_job(session, job_id)
    _require_running(job)
    job.status = "FAILED"
    job.error = error
    job.finished_at = datetime.now(timezone.utc)
    session.flush()
    return job


def _locked_job(session: Session, job_id: int) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise JobStateError("Job does not exist")
    return job


def _require_running(job: Job) -> None:
    if job.status != "RUNNING":
        raise JobStateError("Job must be RUNNING")
