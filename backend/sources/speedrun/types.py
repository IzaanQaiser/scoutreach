from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SpeedrunScope = Literal["speedrun", "portfolio", "everywhere"]
SpeedrunTier = Literal["speedrun", "a16z", "market", "universe"]
SpeedrunCompPeriod = Literal["year", "hour", "month", "week", "day"]


class SpeedrunCompany(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str
    url: str
    tier: str
    open_roles: int
    cohort: str | None = None
    location: str | None = None
    industries: list[str] = Field(default_factory=list)
    blurb: str | None = None
    logo: str | None = None


class SpeedrunCompanyJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    url: str
    location: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    comp_summary: str | None = None
    comp_min: float | None = None
    comp_max: float | None = None
    comp_period: str | None = None
    published_at: str | None = None


class SpeedrunCompanyWithJobs(SpeedrunCompany):
    jobs: list[SpeedrunCompanyJob]


class SpeedrunJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    company: str
    url: str
    remote: bool
    stealth: bool
    company_slug: str | None = None
    company_url: str | None = None
    location: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    function: str | None = None
    seniority: str | None = None
    comp_min: float | None = None
    comp_max: float | None = None
    comp_currency: str | None = None
    comp_period: SpeedrunCompPeriod | None = None
    published_at: str | None = None
    cohort: str | None = None
    tier: SpeedrunTier | None = None


class SpeedrunFacetValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    v: str
    n: int


class SpeedrunFacets(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fn: list[SpeedrunFacetValue] | None = None
    sen: list[SpeedrunFacetValue] | None = None
    emp: list[SpeedrunFacetValue] | None = None
    cohort: list[SpeedrunFacetValue] | None = None
    portfolio: list[SpeedrunFacetValue] | None = None
    loc: list[SpeedrunFacetValue] | None = None
    compAvailable: int | None = None
    compHidden: int | None = None
    stealth: int | None = None
    named: int | None = None


class SpeedrunCompanyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: SpeedrunCompanyWithJobs
    source: str | None = None


class SpeedrunCompaniesPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    companies: list[SpeedrunCompany]
    total: int = Field(ge=0)
    page: int = Field(ge=0)
    page_size: Literal[100]
    total_pages: int = Field(ge=0)
    source: str | None = None


class SpeedrunJobSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jobs: list[SpeedrunJob]
    total: int = Field(ge=0)
    page: int = Field(ge=0)
    page_size: Literal[50]
    total_pages: int = Field(ge=0)
    facets: SpeedrunFacets
    scope: SpeedrunScope | None = None
    beyond_portfolio: int | None = None
    source: str | None = None
