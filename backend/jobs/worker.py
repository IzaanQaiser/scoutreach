import argparse
import time
from collections.abc import Callable, Mapping

from sqlalchemy.orm import Session, sessionmaker

from backend.db.repositories.job import claim_next, fail, succeed
from backend.db.session import create_db_engine, create_session_factory


JobHandler = Callable[[int, dict[str, object]], None]
_handlers: dict[str, JobHandler] = {}


class UnknownJobTypeError(RuntimeError):
    pass


def register_handler(job_type: str, handler: JobHandler) -> None:
    _handlers[job_type] = handler


def run_worker_iteration(
    session_factory: sessionmaker[Session],
    handlers: Mapping[str, JobHandler] | None = None,
) -> bool:
    with session_factory.begin() as session:
        job = claim_next(session)
        if job is None:
            return False
        job_id = job.id
        job_type = job.type
        payload = dict(job.payload)

    active_handlers = _handlers if handlers is None else handlers
    try:
        handler = active_handlers.get(job_type)
        if handler is None:
            raise UnknownJobTypeError(f"Unknown job type: {job_type}")
        handler(job_id, payload)
    except Exception as error:
        message = str(error) or error.__class__.__name__
        with session_factory.begin() as session:
            fail(session, job_id, message)
        return True

    with session_factory.begin() as session:
        succeed(session, job_id)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the durable job worker")
    parser.add_argument("--poll-interval", type=float, default=1.0)
    args = parser.parse_args()

    engine = create_db_engine()
    session_factory = create_session_factory(engine)
    try:
        while True:
            worked = run_worker_iteration(session_factory)
            if not worked:
                time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        pass
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
