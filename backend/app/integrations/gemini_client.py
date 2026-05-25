"""Gemini dossier integration contract for Phase 3."""

from __future__ import annotations

from app.integrations.provider_errors import ProviderError


REQUIRED_DOSSIER_FIELDS = (
    "summary",
    "industry",
    "product_overview",
    "hiring_relevance",
    "startup_focus",
    "tech_stack_inferred",
)


class GeminiDossierClient:
    """Deterministic Phase 3 dossier client with response validation."""

    def generate_company_dossier(
        self,
        *,
        company_name: str,
        batch: str,
        tags: list[str],
        founders: list[dict],
        website_content: dict,
        raw_scraped_data: dict,
    ) -> dict:
        payload = self._simulate_provider_response(
            company_name=company_name,
            batch=batch,
            tags=tags,
            founders=founders,
            website_content=website_content,
            raw_scraped_data=raw_scraped_data,
        )
        return self.parse_dossier_response(payload)

    def parse_dossier_response(self, payload: object) -> dict:
        if not isinstance(payload, dict):
            raise ProviderError(
                code="GEMINI_FAILED",
                provider="gemini",
                message="Gemini returned malformed dossier payload.",
            )

        missing_fields = [field for field in REQUIRED_DOSSIER_FIELDS if field not in payload]
        if missing_fields:
            raise ProviderError(
                code="GEMINI_FAILED",
                provider="gemini",
                message=f"Gemini dossier missing required fields: {', '.join(missing_fields)}.",
            )

        normalized: dict[str, object] = {}
        for field in REQUIRED_DOSSIER_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ProviderError(
                    code="GEMINI_FAILED",
                    provider="gemini",
                    message=f"Gemini dossier field '{field}' is empty or invalid.",
                )
            normalized[field] = value.strip()

        raw_tags = payload.get("generated_tags", [])
        if not isinstance(raw_tags, list):
            raise ProviderError(
                code="GEMINI_FAILED",
                provider="gemini",
                message="Gemini dossier field 'generated_tags' must be a list.",
            )

        normalized_tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
        normalized["generated_tags"] = normalized_tags

        return normalized

    def _simulate_provider_response(
        self,
        *,
        company_name: str,
        batch: str,
        tags: list[str],
        founders: list[dict],
        website_content: dict,
        raw_scraped_data: dict,
    ) -> dict:
        if "dossier-fail" in company_name.lower() or raw_scraped_data.get("force_dossier_fail") is True:
            raise ProviderError(
                code="GEMINI_FAILED",
                provider="gemini",
                message="Gemini dossier generation failed (simulated).",
            )

        founder_names = [str(founder.get("name", "")).strip() for founder in founders if founder.get("name")]

        return {
            "summary": f"{company_name} builds products for fast-moving teams.",
            "industry": "Software",
            "product_overview": "Workflow tooling for technical organizations.",
            "hiring_relevance": "Potential fit for engineering and product candidates.",
            "startup_focus": f"YC {batch} company focused on shipping velocity.",
            "tech_stack_inferred": "Python, TypeScript, Postgres, APIs",
            "generated_tags": sorted(set([*tags, "b2b", "saas"])),
            "founder_context": founder_names,
            "content_source": {
                "website_pages_scraped": len(website_content.keys()),
                "raw_source": raw_scraped_data.get("source"),
            },
        }
