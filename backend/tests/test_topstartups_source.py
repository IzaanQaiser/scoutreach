from pathlib import Path

import httpx
import pytest

from backend.sources.topstartups import (
    TopStartupsAccessError,
    TopStartupsClient,
    TopStartupsParseError,
)


FIXTURES = Path(__file__).parent / "fixtures" / "topstartups"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def make_client(handler, *, sleeper=lambda delay: None, delay: float = 0.5):
    return TopStartupsClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        timeout=3.0,
        delay=delay,
        sleeper=sleeper,
    )


def test_normal_parse_preserves_provenance_and_explicit_series_a() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://topstartups.io/?page=1"
        assert "Scoutreach" in request.headers["User-Agent"]
        assert "cookie" not in request.headers
        return httpx.Response(200, text=fixture("page1.html"))

    company = make_client(handler).fetch_companies(limit=1, max_pages=1)[0]

    assert company.name == "Alpha AI"
    assert company.website == "https://www.alpha.example/?utm_source=topstartups.io"
    assert company.domain == "alpha.example"
    assert company.description == "Builds careful AI infrastructure."
    assert company.categories == ["AI", "Developer Tools"]
    assert company.location == "New York, USA"
    assert company.funding_text == "Sequoia Series A in 2025"
    assert company.stage == "Series A"
    assert company.source_url == "https://topstartups.io/?page=1"


def test_missing_optional_fields_are_valid() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture("missing_optional.html"))

    company = make_client(handler).fetch_companies(limit=1, max_pages=1)[0]

    assert company.description is None
    assert company.categories == []
    assert company.location is None
    assert company.funding_text is None
    assert company.stage is None


def test_unknown_funding_keeps_raw_text_without_inferred_stage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture("unknown_funding.html"))

    company = make_client(handler).fetch_companies(limit=1, max_pages=1)[0]

    assert company.funding_text == (
        "Raised $12M from Example Ventures at a $100M valuation"
    )
    assert company.stage is None


def test_paginates_from_one_then_stops_at_limit_with_delay_between_requests() -> None:
    requested_pages: list[int] = []
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        requested_pages.append(page)
        return httpx.Response(200, text=fixture(f"page{page}.html"))

    companies = make_client(handler, sleeper=delays.append, delay=0.75).fetch_companies(
        limit=3,
        max_pages=10,
    )

    assert [company.name for company in companies] == ["Alpha AI", "Beta", "Gamma"]
    assert requested_pages == [1, 2]
    assert delays == [0.75]
    assert companies[-1].source_url == "https://topstartups.io/?page=2"


@pytest.mark.parametrize("status_code", [403, 429])
def test_access_denial_stops_without_retry(status_code: int) -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(status_code, text="denied")

    with pytest.raises(TopStartupsAccessError):
        make_client(handler).fetch_companies(limit=2, max_pages=2)
    assert requests == 1


def test_robots_disallowed_response_is_access_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Robots-Policy": "disallow"})

    with pytest.raises(TopStartupsAccessError):
        make_client(handler).fetch_companies(limit=1, max_pages=1)


def test_malformed_startup_card_is_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture("malformed.html"))

    with pytest.raises(TopStartupsParseError, match="name/site structure"):
        make_client(handler).fetch_companies(limit=1, max_pages=1)


def test_changed_startup_card_wrapper_is_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture("changed_wrapper.html"))

    with pytest.raises(TopStartupsParseError, match="layout is unsupported"):
        make_client(handler).fetch_companies(limit=1, max_pages=1)


@pytest.mark.parametrize("limit", [0, 201])
def test_invalid_limits_are_rejected_before_request(limit: int) -> None:
    def unexpected_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP request should not be made")

    with pytest.raises(ValueError, match="between 1 and 200"):
        make_client(unexpected_request).fetch_companies(limit=limit, max_pages=1)


def test_more_than_ten_pages_is_rejected_before_request() -> None:
    def unexpected_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP request should not be made")

    with pytest.raises(ValueError, match="between 1 and 10"):
        make_client(unexpected_request).fetch_companies(limit=1, max_pages=11)
