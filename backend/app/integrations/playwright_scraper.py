"""Phase 2/3 scraper integration entrypoint.

This remains deterministic for local/test behavior.
Real Playwright network scraping is deferred.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ScrapedCompany:
    batch: str
    name: str
    yc_url: str
    website_url: str
    domain: str
    founders: list[dict]
    raw_scraped_data: dict
    scrape_failed: bool = False
    failure_reason: str | None = None


class PlaywrightYcScraper:
    """Stub scraper contract for pipeline wiring."""

    def scrape_batches(self, selected_batches: list[str]) -> Iterable[ScrapedCompany]:
        for batch in selected_batches:
            normalized_batch = batch.strip().upper()
            slug = normalized_batch.lower().replace(" ", "-")

            # Controlled partial scrape failure path.
            if normalized_batch == "FAIL_ONE":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Failure Co ({normalized_batch})",
                    yc_url=f"https://www.ycombinator.com/companies/failure-{slug}",
                    website_url="",
                    domain="",
                    founders=[],
                    raw_scraped_data={"batch": normalized_batch},
                    scrape_failed=True,
                    failure_reason="Simulated company scrape failure.",
                )

            if normalized_batch == "DOSSIER_FAIL":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Dossier-Fail {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/dossier-fail-{slug}",
                    website_url=f"https://dossier-fail-{slug}.com",
                    domain=f"dossier-fail-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            if normalized_batch == "HUNTER_EMPTY":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Hunter Empty {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/hunter-empty-{slug}",
                    website_url=f"https://hunter-empty-{slug}.com",
                    domain=f"hunter-empty-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            if normalized_batch == "HUNTER_ERROR":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Hunter Error {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/hunter-error-{slug}",
                    website_url=f"https://hunter-error-{slug}.com",
                    domain=f"hunter-error-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            if normalized_batch == "HUNTER_429":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Hunter Rate Limit {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/hunter-rate-limit-{slug}",
                    website_url=f"https://hunter-429-{slug}.com",
                    domain=f"hunter-429-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            if normalized_batch == "HUNTER_5XX":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Hunter Transient {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/hunter-transient-{slug}",
                    website_url=f"https://hunter-5xx-{slug}.com",
                    domain=f"hunter-5xx-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            if normalized_batch == "MESSAGE_429":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Message 429 {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/message-429-{slug}",
                    website_url=f"https://message-429-{slug}.com",
                    domain=f"message-429-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            if normalized_batch == "MESSAGE_5XX":
                yield ScrapedCompany(
                    batch=normalized_batch,
                    name=f"Message 5xx {normalized_batch} Labs",
                    yc_url=f"https://www.ycombinator.com/companies/message-5xx-{slug}",
                    website_url=f"https://message-5xx-{slug}.com",
                    domain=f"message-5xx-{slug}.com",
                    founders=[{"name": f"Founder {normalized_batch}"}],
                    raw_scraped_data={"source": "phase_stub", "batch": normalized_batch},
                )
                continue

            yield ScrapedCompany(
                batch=normalized_batch,
                name=f"Example {normalized_batch} Labs",
                yc_url=f"https://www.ycombinator.com/companies/example-{slug}",
                website_url=f"https://example-{slug}.com",
                domain=f"example-{slug}.com",
                founders=[
                    {
                        "name": f"Founder {normalized_batch}",
                        "linkedin_url": f"https://linkedin.com/in/founder-{slug}",
                    }
                ],
                raw_scraped_data={
                    "source": "phase_stub",
                    "batch": normalized_batch,
                },
            )
