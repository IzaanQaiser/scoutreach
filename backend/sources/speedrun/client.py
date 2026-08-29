from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from backend.sources.speedrun.exceptions import (
    SpeedrunHTTPError,
    SpeedrunProviderError,
    SpeedrunResponseError,
    SpeedrunTimeoutError,
)
from backend.sources.speedrun.types import (
    SpeedrunCompaniesPage,
    SpeedrunCompany,
    SpeedrunCompanyDetail,
    SpeedrunJob,
    SpeedrunJobSearchResult,
    SpeedrunScope,
)


BASE_URL = "https://speedrun-talent-network.com/api/v1"
MAX_RESULTS = 500
DEFAULT_TIMEOUT_SECONDS = 10.0

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class SpeedrunClient:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._http_client = http_client or httpx.Client()
        self._timeout = timeout

    def list_companies(self, limit: int) -> list[SpeedrunCompany]:
        _validate_limit(limit)
        companies: list[SpeedrunCompany] = []
        page_number = 0

        while len(companies) < limit:
            page = self._companies_page(page_number)
            companies.extend(page.companies)
            if len(companies) >= limit or page.page + 1 >= page.total_pages:
                break
            page_number += 1

        return companies[:limit]

    def get_company(self, slug: str) -> SpeedrunCompanyDetail:
        data = self._request(f"/companies/{quote(slug, safe='')}")
        return _parse_response(data, SpeedrunCompanyDetail)

    def search_jobs(
        self,
        *,
        limit: int,
        q: str | None = None,
        company: str | None = None,
        scope: SpeedrunScope | None = None,
    ) -> list[SpeedrunJob]:
        _validate_limit(limit)
        jobs: list[SpeedrunJob] = []
        page_number = 0

        while len(jobs) < limit:
            page = self._jobs_page(
                page=page_number,
                q=q,
                company=company,
                scope=scope,
            )
            jobs.extend(page.jobs)
            if len(jobs) >= limit or page.page + 1 >= page.total_pages:
                break
            page_number += 1

        return jobs[:limit]

    def _companies_page(self, page: int) -> SpeedrunCompaniesPage:
        data = self._request("/companies", params={"page": page})
        result = _parse_response(data, SpeedrunCompaniesPage)
        if result.page != page:
            raise SpeedrunResponseError("Speedrun response returned an unexpected page")
        return result

    def _jobs_page(
        self,
        *,
        page: int,
        q: str | None,
        company: str | None,
        scope: str | None,
    ) -> SpeedrunJobSearchResult:
        params: dict[str, str | int] = {"page": page}
        if q is not None:
            params["q"] = q
        if company is not None:
            params["company"] = company
        if scope is not None:
            params["scope"] = scope
        data = self._request("/jobs", params=params)
        result = _parse_response(data, SpeedrunJobSearchResult)
        if result.page != page:
            raise SpeedrunResponseError("Speedrun response returned an unexpected page")
        return result

    def _request(
        self,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> object:
        request_params = dict(params or {})
        request_params["source"] = "scoutreach"
        try:
            response = self._http_client.get(
                f"{BASE_URL}{path}",
                params=request_params,
                timeout=self._timeout,
            )
        except httpx.TimeoutException:
            raise SpeedrunTimeoutError("Speedrun request timed out") from None
        except httpx.RequestError:
            raise SpeedrunHTTPError(0) from None

        try:
            data = response.json()
        except ValueError:
            raise SpeedrunResponseError("Speedrun returned malformed JSON") from None

        provider_error = _provider_error(data)
        if provider_error is not None:
            code, message = provider_error
            raise SpeedrunProviderError(code, message, response.status_code)
        if not 200 <= response.status_code < 300:
            raise SpeedrunHTTPError(response.status_code)
        return data


def _validate_limit(limit: int) -> None:
    if not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"limit must be between 1 and {MAX_RESULTS}")


def _parse_response(data: object, model: type[ResponseModel]) -> ResponseModel:
    try:
        return model.model_validate(data)
    except ValidationError:
        raise SpeedrunResponseError("Speedrun returned a malformed response") from None


def _provider_error(data: object) -> tuple[str, str] | None:
    if not isinstance(data, dict) or "error" not in data:
        return None
    error = data["error"]
    if not isinstance(error, dict):
        raise SpeedrunResponseError("Speedrun returned a malformed error response")
    code = error.get("code")
    message = error.get("message")
    if not isinstance(code, str) or not isinstance(message, str):
        raise SpeedrunResponseError("Speedrun returned a malformed error response")
    return code, message
