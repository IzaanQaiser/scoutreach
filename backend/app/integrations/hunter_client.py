"""Hunter enrichment integration contract for Phase 3."""

from __future__ import annotations

import re

from app.integrations.provider_errors import ProviderError


class HunterEmailClient:
    """Deterministic Phase 3 enrichment client for founder email lookups."""

    def enrich_founders(self, *, founders: list[dict], domain: str) -> list[dict]:
        normalized_domain = (domain or "").strip().lower()

        if "hunter-error" in normalized_domain:
            raise ProviderError(
                code="HUNTER_FAILED",
                provider="hunter",
                message="Hunter lookup failed (simulated).",
            )

        if "hunter-429" in normalized_domain:
            raise ProviderError(
                code="HUNTER_RATE_LIMITED",
                provider="hunter",
                message="Hunter lookup rate limited (simulated).",
            )

        if "hunter-5xx" in normalized_domain:
            raise ProviderError(
                code="HUNTER_TRANSIENT",
                provider="hunter",
                message="Hunter transient provider failure (simulated).",
            )

        enriched: list[dict] = []
        for founder in founders:
            normalized = dict(founder)
            normalized["email_lookup_provider"] = "hunter"

            if "hunter-empty" in normalized_domain or not normalized_domain:
                normalized["email_lookup_status"] = "empty"
                normalized["email"] = None
                normalized["email_confidence"] = None
            else:
                local_part = self._slugify_local_part(str(normalized.get("name", "founder")))
                normalized["email_lookup_status"] = "success"
                normalized["email"] = f"{local_part}@{normalized_domain}"
                normalized["email_confidence"] = 0.88

            enriched.append(normalized)

        return enriched

    def mark_lookup_failed(self, *, founders: list[dict], error_message: str) -> list[dict]:
        marked: list[dict] = []
        for founder in founders:
            normalized = dict(founder)
            normalized["email_lookup_provider"] = "hunter"
            normalized["email_lookup_status"] = "failed"
            normalized["email_lookup_error"] = error_message
            normalized["email"] = None
            normalized["email_confidence"] = None
            marked.append(normalized)
        return marked

    def _slugify_local_part(self, value: str) -> str:
        lowered = value.strip().lower()
        compact = re.sub(r"[^a-z0-9]+", ".", lowered)
        compact = compact.strip(".")
        return compact or "founder"
