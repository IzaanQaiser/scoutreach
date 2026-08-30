import time
from collections.abc import Callable

import httpx

from backend.sources.topstartups.exceptions import (
    TopStartupsAccessError,
    TopStartupsHTTPError,
)
from backend.sources.topstartups.parser import parse_companies_page
from backend.sources.topstartups.types import TopStartupsCompany


BASE_URL = "https://topstartups.io/"
USER_AGENT = "Scoutreach/1.0 public startup-listing research client"
DEFAULT_TIMEOUT_SECONDS = 10.0
MIN_DELAY_SECONDS = 0.5


class TopStartupsClient:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        delay: float = MIN_DELAY_SECONDS,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if delay < MIN_DELAY_SECONDS:
            raise ValueError("delay must be at least 0.5 seconds")
        self._http_client = http_client or httpx.Client()
        self._timeout = timeout
        self._delay = delay
        self._sleeper = sleeper

    def fetch_companies(
        self,
        limit: int,
        max_pages: int,
    ) -> list[TopStartupsCompany]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if not 1 <= max_pages <= 10:
            raise ValueError("max_pages must be between 1 and 10")

        companies: list[TopStartupsCompany] = []
        page = 1
        while page <= max_pages and len(companies) < limit:
            if page > 1:
                self._sleeper(self._delay)
            source_url = f"{BASE_URL}?page={page}"
            response = self._get(source_url)
            page_companies, has_next = parse_companies_page(
                response.text,
                source_url=source_url,
            )
            if not page_companies:
                break
            companies.extend(page_companies)
            if len(companies) >= limit or not has_next:
                break
            page += 1

        return companies[:limit]

    def _get(self, url: str) -> httpx.Response:
        try:
            response = self._http_client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=self._timeout,
            )
        except httpx.RequestError:
            raise TopStartupsHTTPError() from None

        if response.status_code in {403, 429} or _robots_disallowed(response):
            raise TopStartupsAccessError("TopStartups public listing access denied")
        if not 200 <= response.status_code < 300:
            raise TopStartupsHTTPError(response.status_code)
        return response


def _robots_disallowed(response: httpx.Response) -> bool:
    allowed = response.headers.get("X-Robots-Allowed", "").casefold()
    policy = response.headers.get("Robots-Policy", "").casefold()
    if allowed in {"0", "false", "no"} or "disallow" in policy:
        return True
    sample = response.text[:4096].casefold()
    return "robots.txt" in sample and "disallow" in sample
