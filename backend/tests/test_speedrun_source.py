import httpx
import pytest

from backend.sources.speedrun import (
    MAX_RESULTS,
    SpeedrunClient,
    SpeedrunCompanyDetail,
    SpeedrunHTTPError,
    SpeedrunProviderError,
    SpeedrunResponseError,
    SpeedrunTimeoutError,
)


def make_client(handler) -> SpeedrunClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(
        transport=transport,
        base_url="https://speedrun-talent-network.com/api/v1",
    )
    return SpeedrunClient(http_client=http_client, timeout=2.5)


def test_company_detail_is_typed_and_includes_live_jobs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/companies/acme"
        assert request.url.params["source"] == "scoutreach"
        return httpx.Response(
            200,
            json={
                "company": {
                    "slug": "acme",
                    "name": "Acme",
                    "url": "https://speedrun-talent-network.com/companies/acme",
                    "tier": "speedrun",
                    "open_roles": 1,
                    "cohort": "SR007",
                    "location": "San Francisco",
                    "industries": ["developer-tools"],
                    "blurb": "Developer infrastructure.",
                    "logo": None,
                    "jobs": [
                        {
                            "id": "job-1",
                            "title": "Engineer",
                            "url": "https://speedrun-talent-network.com/jobs/job-1",
                            "location": "San Francisco",
                            "workplace_type": "Hybrid",
                            "employment_type": "FullTime",
                            "comp_summary": "$150k-$180k",
                            "comp_min": 150000,
                            "comp_max": 180000,
                            "comp_period": "year",
                            "published_at": "2026-08-29T00:00:00Z",
                        }
                    ],
                },
                "source": "scoutreach",
            },
        )

    detail = make_client(handler).get_company("acme")

    assert isinstance(detail, SpeedrunCompanyDetail)
    assert detail.company.slug == "acme"
    assert detail.company.jobs[0].title == "Engineer"
    assert detail.source == "scoutreach"


def test_companies_pagination_honors_limit_without_extra_page() -> None:
    requested_pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        requested_pages.append(page)
        assert request.url.params["source"] == "scoutreach"
        companies = [
            {
                "slug": f"company-{page}-{index}",
                "name": f"Company {index}",
                "url": (
                    "https://speedrun-talent-network.com/companies/"
                    f"company-{page}-{index}"
                ),
                "tier": "speedrun",
                "open_roles": 1,
            }
            for index in range(100)
        ]
        return httpx.Response(
            200,
            json={
                "companies": companies,
                "total": 300,
                "page": page,
                "page_size": 100,
                "total_pages": 3,
                "source": "scoutreach",
            },
        )

    companies = make_client(handler).list_companies(150)

    assert len(companies) == 150
    assert requested_pages == [0, 1]


def test_jobs_pagination_filters_and_limit_without_extra_page() -> None:
    requested_pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        requested_pages.append(page)
        assert request.url.params["source"] == "scoutreach"
        assert request.url.params["q"] == "engineer"
        assert request.url.params["company"] == "acme"
        assert request.url.params["scope"] == "speedrun"
        jobs = [
            {
                "id": f"job-{page}-{index}",
                "title": f"Engineer {index}",
                "company": "Acme",
                "url": (
                    "https://speedrun-talent-network.com/jobs/"
                    f"job-{page}-{index}"
                ),
                "remote": True,
                "stealth": False,
                "company_slug": "acme",
                "company_url": (
                    "https://speedrun-talent-network.com/companies/acme"
                ),
                "location": "Remote",
                "workplace_type": "Remote",
                "employment_type": "FullTime",
                "function": "engineering",
                "seniority": "senior",
                "comp_min": 150000,
                "comp_max": 200000,
                "comp_currency": "USD",
                "comp_period": "year",
                "published_at": "2026-08-29T00:00:00Z",
                "cohort": "SR007",
                "tier": "speedrun",
            }
            for index in range(50)
        ]
        return httpx.Response(
            200,
            json={
                "jobs": jobs,
                "total": 150,
                "page": page,
                "page_size": 50,
                "total_pages": 3,
                "facets": {
                    "fn": [{"v": "engineering", "n": 150}],
                    "sen": [{"v": "senior", "n": 75}],
                    "emp": [{"v": "FullTime", "n": 150}],
                    "cohort": [{"v": "SR007", "n": 50}],
                    "portfolio": [{"v": "speedrun", "n": 150}],
                    "loc": [{"v": "remote", "n": 150}],
                    "compAvailable": 100,
                    "compHidden": 50,
                    "stealth": 0,
                    "named": 150,
                },
                "scope": "speedrun",
                "beyond_portfolio": 20,
                "source": "scoutreach",
            },
        )

    jobs = make_client(handler).search_jobs(
        q="engineer",
        company="acme",
        scope="speedrun",
        limit=75,
    )

    assert len(jobs) == 75
    assert requested_pages == [0, 1]


def test_timeout_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("secret raw timeout", request=request)

    with pytest.raises(SpeedrunTimeoutError, match="timed out") as error:
        make_client(handler).list_companies(1)
    assert "secret raw timeout" not in str(error.value)


def test_provider_error_is_normalized_without_raw_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={
                "error": {"code": "rate_limited", "message": "Try later"},
                "raw": "secret-body",
            },
        )

    with pytest.raises(SpeedrunProviderError) as error:
        make_client(handler).list_companies(1)
    assert error.value.code == "rate_limited"
    assert error.value.provider_message == "Try later"
    assert "secret-body" not in str(error.value)


def test_non_2xx_without_provider_error_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "secret-body"})

    with pytest.raises(SpeedrunHTTPError) as error:
        make_client(handler).list_companies(1)
    assert error.value.status_code == 503
    assert "secret-body" not in str(error.value)


def test_malformed_response_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "companies": "not-a-list",
                "total": 1,
                "page": 0,
                "page_size": 100,
                "total_pages": 1,
                "source": "scoutreach",
            },
        )

    with pytest.raises(SpeedrunResponseError, match="malformed response"):
        make_client(handler).list_companies(1)


@pytest.mark.parametrize("limit", [0, MAX_RESULTS + 1])
def test_company_and_job_limits_are_rejected_before_request(limit: int) -> None:
    def unexpected_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP request should not be made")

    client = make_client(unexpected_request)

    with pytest.raises(ValueError, match="between 1 and 500"):
        client.list_companies(limit)
    with pytest.raises(ValueError, match="between 1 and 500"):
        client.search_jobs(limit=limit)
