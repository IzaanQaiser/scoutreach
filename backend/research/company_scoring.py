import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from backend.models.company import Company


_TOKENS = re.compile(r"[a-z0-9]+")
_ENGINEERING_TERMS = (
    ("engineering",),
    ("engineer",),
    ("software",),
    ("developer",),
    ("backend",),
    ("back", "end"),
    ("frontend",),
    ("front", "end"),
    ("fullstack",),
    ("full", "stack"),
    ("platform",),
    ("infrastructure",),
    ("infra",),
    ("data",),
    ("machine", "learning"),
    ("ml",),
    ("artificial", "intelligence"),
    ("ai",),
)
_NON_ENGINEERING_ROLE_TERMS = (
    ("recruiter",),
    ("recruiting",),
    ("talent",),
    ("sales",),
    ("account", "executive"),
    ("marketing",),
    ("customer", "success"),
)
_EARLY_CAREER_TERMS = (
    ("intern",),
    ("internship",),
    ("junior",),
    ("new", "grad"),
    ("entry", "level"),
)
_TECHNICAL_GROUPS = (
    (
        "software",
        (("software",), ("developer",), ("engineering",)),
    ),
    (
        "ai_ml",
        (
            ("ai",),
            ("ml",),
            ("artificial", "intelligence"),
            ("machine", "learning"),
        ),
    ),
    ("data", (("data",),)),
    (
        "infra_cloud",
        (("infrastructure",), ("infra",), ("cloud",)),
    ),
)


class CompanyScoreJob(Protocol):
    title: str
    function: str | None
    location: str | None
    active: bool


@dataclass(frozen=True)
class CompanyScoreInput:
    names: tuple[str, ...]
    stages: tuple[str, ...]
    locations: tuple[str, ...]
    descriptions: tuple[str, ...]
    categories: tuple[str, ...]


@dataclass(frozen=True)
class CompanyScoreReason:
    code: str
    points: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class CompanyScore:
    score: int
    reasons: tuple[CompanyScoreReason, ...]


def build_company_score_input(companies: Iterable[Company]) -> CompanyScoreInput:
    company_rows = tuple(companies)
    metadata_categories: list[str] = []
    for company in company_rows:
        metadata = company.source_metadata
        if not isinstance(metadata, dict):
            continue
        for key in ("categories", "industries"):
            values = metadata.get(key)
            if isinstance(values, list):
                metadata_categories.extend(
                    value for value in values if isinstance(value, str)
                )

    return CompanyScoreInput(
        names=_stable_strings(company.name for company in company_rows),
        stages=_stable_strings(company.stage for company in company_rows),
        locations=_stable_strings(company.location for company in company_rows),
        descriptions=_stable_strings(
            company.description for company in company_rows
        ),
        categories=_stable_strings(metadata_categories),
    )


def score_company(
    company: CompanyScoreInput,
    jobs: Iterable[CompanyScoreJob],
) -> CompanyScore:
    job_rows = tuple(jobs)
    active_jobs = tuple(job for job in job_rows if job.active)
    reasons: list[CompanyScoreReason] = []

    engineering_jobs = tuple(
        job for job in active_jobs if _is_engineering_job(job)
    )
    if engineering_jobs:
        points = 50 + min(max(len(engineering_jobs) - 1, 0) * 5, 10)
        reasons.append(
            CompanyScoreReason(
                code="active_engineering_jobs",
                points=points,
                evidence=_stable_strings(job.title for job in engineering_jobs),
            )
        )

    early_career_jobs = tuple(
        job for job in active_jobs if _matches(job.title, _EARLY_CAREER_TERMS)
    )
    if early_career_jobs:
        reasons.append(
            CompanyScoreReason(
                code="active_early_career_jobs",
                points=20,
                evidence=_stable_strings(job.title for job in early_career_jobs),
            )
        )

    qualifying_stages = tuple(
        stage for stage in company.stages if _is_growth_stage(stage)
    )
    if qualifying_stages:
        reasons.append(
            CompanyScoreReason(
                code="growth_stage",
                points=10,
                evidence=_stable_strings(qualifying_stages),
            )
        )

    matching_locations = list(
        location for location in company.locations if _is_target_location(location)
    )
    matching_locations.extend(
        job.location
        for job in active_jobs
        if job.location and _is_target_location(job.location)
    )
    if matching_locations:
        reasons.append(
            CompanyScoreReason(
                code="target_location",
                points=10,
                evidence=_stable_strings(matching_locations),
            )
        )

    technical_text = (
        *company.names,
        *company.descriptions,
        *company.categories,
    )
    matched_groups = tuple(
        group_name
        for group_name, terms in _TECHNICAL_GROUPS
        if any(_matches(value, terms) for value in technical_text)
    )
    if matched_groups:
        reasons.append(
            CompanyScoreReason(
                code="technical_groups",
                points=min(len(matched_groups) * 5, 20),
                evidence=matched_groups,
            )
        )

    return CompanyScore(
        score=sum(reason.points for reason in reasons),
        reasons=tuple(reasons),
    )


def _is_engineering_job(job: CompanyScoreJob) -> bool:
    role_text = " ".join(value for value in (job.function, job.title) if value)
    return _matches(role_text, _ENGINEERING_TERMS) and not _matches(
        role_text,
        _NON_ENGINEERING_ROLE_TERMS,
    )


def _is_growth_stage(stage: str) -> bool:
    tokens = _tokenize(stage)
    return (
        len(tokens) >= 2
        and tokens[0] == "series"
        and tokens[1] in set("abcdefg")
    ) or tokens[:2] == ("post", "ipo")


def _is_target_location(location: str) -> bool:
    tokens = _tokenize(location)
    return any(
        _contains_phrase(tokens, phrase)
        for phrase in (("san", "francisco"), ("bay", "area"), ("remote",))
    )


def _matches(value: str, phrases: Sequence[tuple[str, ...]]) -> bool:
    tokens = _tokenize(value)
    return any(_contains_phrase(tokens, phrase) for phrase in phrases)


def _contains_phrase(tokens: tuple[str, ...], phrase: tuple[str, ...]) -> bool:
    width = len(phrase)
    return any(
        tokens[index : index + width] == phrase
        for index in range(len(tokens) - width + 1)
    )


def _tokenize(value: str) -> tuple[str, ...]:
    return tuple(_TOKENS.findall(value.casefold()))


def _stable_strings(values: Iterable[str | None]) -> tuple[str, ...]:
    cleaned = {
        stripped
        for value in values
        if value is not None and (stripped := value.strip())
    }
    return tuple(sorted(cleaned, key=lambda value: (value.casefold(), value)))
