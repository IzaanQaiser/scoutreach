from __future__ import annotations

import pytest

from app.integrations.gemini_client import GeminiDossierClient
from app.integrations.provider_errors import ProviderError


def test_parse_dossier_response_accepts_valid_payload() -> None:
    client = GeminiDossierClient()
    payload = {
        "summary": "  Productive collaboration suite. ",
        "industry": "Software",
        "product_overview": "Team workflow tools",
        "hiring_relevance": "High signal for technical candidates",
        "startup_focus": "Early-stage product velocity",
        "tech_stack_inferred": "Python, TypeScript",
        "generated_tags": ["saas", "", "b2b"],
    }

    parsed = client.parse_dossier_response(payload)

    assert parsed["summary"] == "Productive collaboration suite."
    assert parsed["industry"] == "Software"
    assert parsed["generated_tags"] == ["saas", "b2b"]


def test_parse_dossier_response_rejects_missing_required_fields() -> None:
    client = GeminiDossierClient()

    with pytest.raises(ProviderError) as exc_info:
        client.parse_dossier_response({"summary": "Only summary provided"})

    assert exc_info.value.code == "GEMINI_FAILED"
    assert "missing required fields" in exc_info.value.message
