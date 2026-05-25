"""Shared provider exception types for external integrations."""

from __future__ import annotations


class ProviderError(Exception):
    def __init__(self, *, code: str, provider: str, message: str) -> None:
        self.code = code
        self.provider = provider
        self.message = message
        super().__init__(message)
