"""Gmail sending integration contract for Phase 6."""

from __future__ import annotations

from app.integrations.provider_errors import ProviderError


class GmailClient:
    """Deterministic Gmail sender for local/test workflows."""

    def send_message(
        self,
        *,
        outreach_id: str,
        to_email: str | None,
        subject: str | None,
        message_content: str | None,
    ) -> dict:
        email = (to_email or "").strip().lower()
        message_subject = (subject or "").strip()
        body = (message_content or "").strip()

        if not email:
            raise ProviderError(
                code="GMAIL_FAILED",
                provider="gmail",
                message="Gmail send failed: missing recipient email.",
            )

        if not message_subject or not body:
            raise ProviderError(
                code="GMAIL_FAILED",
                provider="gmail",
                message="Gmail send failed: subject or body is empty.",
            )

        if "gmail-429" in email:
            raise ProviderError(
                code="GMAIL_RATE_LIMITED",
                provider="gmail",
                message="Gmail API rate limited request (simulated).",
            )

        if "gmail-5xx" in email:
            raise ProviderError(
                code="GMAIL_TRANSIENT",
                provider="gmail",
                message="Gmail transient provider error (simulated).",
            )

        if "gmail-fail" in email:
            raise ProviderError(
                code="GMAIL_FAILED",
                provider="gmail",
                message="Gmail send failed (simulated).",
            )

        return {
            "provider_message_id": f"gmail-{outreach_id}",
        }
