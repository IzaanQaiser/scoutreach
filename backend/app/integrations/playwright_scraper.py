"""Phase 2 scraper integration entrypoint.

This intentionally returns deterministic mock scrape outputs for now.
Actual Playwright network scraping is deferred to a later phase.
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
    """Stub scraper contract for Phase 2 pipeline wiring."""

    def scrape_batches(self, selected_batches: list[str]) -> Iterable[ScrapedCompany]:
        for batch in selected_batches:
            normalized_batch = batch.strip().upper()
            slug = normalized_batch.lower().replace(" ", "-")

            # Inject one controlled partial failure path for testing and resiliency validation.
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
                    "source": "phase2_stub",
                    "batch": normalized_batch,
                },
            )

