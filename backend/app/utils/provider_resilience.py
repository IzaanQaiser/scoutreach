"""Retry/backoff helpers for provider calls."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from app.integrations.provider_errors import ProviderError


T = TypeVar("T")


def call_with_backoff(
    *,
    operation: Callable[[], T],
    retryable_codes: set[str],
    max_attempts: int,
    base_delay_seconds: float,
    max_jitter_seconds: float,
) -> T:
    attempts = max(max_attempts, 1)
    base_delay = max(base_delay_seconds, 0)
    max_jitter = max(max_jitter_seconds, 0)

    attempt = 1
    while True:
        try:
            return operation()
        except ProviderError as exc:
            if attempt >= attempts or exc.code not in retryable_codes:
                raise

            backoff_delay = base_delay * (2 ** (attempt - 1))
            jitter = random.uniform(0, max_jitter)
            time.sleep(backoff_delay + jitter)
            attempt += 1
