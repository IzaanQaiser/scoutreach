from dataclasses import dataclass
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.company import Company
from backend.models.job_posting import JobPosting


class CompanyCanonicalizationError(RuntimeError):
    pass


class CompanyNotFoundError(CompanyCanonicalizationError):
    pass


class CompanyCanonicalizationAmbiguityError(CompanyCanonicalizationError):
    pass


@dataclass(frozen=True)
class CompanyMergeResult:
    canonical_company_id: int
    merged_company_ids: list[int]


@dataclass(frozen=True)
class CanonicalCompanyView:
    canonical_company_id: int
    member_company_ids: list[int]
    preferred_domain: str | None
    preferred_website: str | None
    jobs: list[JobPosting]
    freshest_job: JobPosting | None


def canonicalize_company(session: Session, company_id: int) -> CompanyMergeResult:
    companies = list(
        session.scalars(select(Company).order_by(Company.id).with_for_update())
    )
    companies_by_id = {company.id: company for company in companies}
    target = companies_by_id.get(company_id)
    if target is None:
        raise CompanyNotFoundError("Company does not exist")

    resolved_roots = {
        company.id: _resolve_root_id(company, companies_by_id) for company in companies
    }
    groups: dict[int, list[Company]] = {}
    for company in companies:
        groups.setdefault(resolved_roots[company.id], []).append(company)

    target_root_id = resolved_roots[target.id]
    target_group = groups[target_root_id]
    target_domains = _group_domains(target_group)
    if len(target_domains) > 1:
        raise CompanyCanonicalizationAmbiguityError(
            "Canonical company group contains conflicting domains"
        )
    target_names = {company.normalized_name for company in target_group}
    matched_root_ids = {target_root_id}

    if target_domains:
        target_domain = next(iter(target_domains))
        matched_root_ids.update(
            root_id
            for root_id, members in groups.items()
            if target_domain in _group_domains(members)
        )
        domainless_name_matches = {
            root_id
            for root_id, members in groups.items()
            if root_id != target_root_id
            and any(
                normalize_domain(member.domain) is None
                and member.normalized_name in target_names
                for member in members
            )
        }
        if domainless_name_matches:
            _ensure_name_fallback_is_unambiguous(groups, target_names)
            matched_root_ids.update(domainless_name_matches)
    else:
        name_matches = {
            root_id
            for root_id, members in groups.items()
            if any(member.normalized_name in target_names for member in members)
        }
        _ensure_name_fallback_is_unambiguous(groups, target_names)
        matched_root_ids.update(name_matches)

    canonical_company_id = min(matched_root_ids)
    merged_members = sorted(
        company.id
        for company in companies
        if resolved_roots[company.id] in matched_root_ids
    )
    for company in companies:
        if company.id not in merged_members:
            continue
        company.canonical_company_id = (
            None if company.id == canonical_company_id else canonical_company_id
        )
    session.flush()

    return CompanyMergeResult(
        canonical_company_id=canonical_company_id,
        merged_company_ids=[
            member_id
            for member_id in merged_members
            if member_id != canonical_company_id
        ],
    )


def get_canonical_company_view(
    session: Session,
    company_id: int,
) -> CanonicalCompanyView:
    companies = list(session.scalars(select(Company).order_by(Company.id)))
    companies_by_id = {company.id: company for company in companies}
    company = companies_by_id.get(company_id)
    if company is None:
        raise CompanyNotFoundError("Company does not exist")

    canonical_company_id = _resolve_root_id(company, companies_by_id)
    members = [
        candidate
        for candidate in companies
        if _resolve_root_id(candidate, companies_by_id) == canonical_company_id
    ]
    member_ids = sorted(member.id for member in members)
    jobs = list(
        session.scalars(
            select(JobPosting)
            .where(JobPosting.company_id.in_(member_ids))
            .order_by(JobPosting.seen_at.desc(), JobPosting.id)
        )
    )
    latest_job_by_company: dict[int, JobPosting] = {}
    for job in jobs:
        latest_job_by_company.setdefault(job.company_id, job)
    preferred_members = sorted(
        members,
        key=lambda member: (
            -latest_job_by_company[member.id].seen_at.timestamp()
            if member.id in latest_job_by_company
            else float("inf"),
            member.id,
        ),
    )

    return CanonicalCompanyView(
        canonical_company_id=canonical_company_id,
        member_company_ids=member_ids,
        preferred_domain=next(
            (member.domain for member in preferred_members if member.domain),
            None,
        ),
        preferred_website=next(
            (member.website for member in preferred_members if member.website),
            None,
        ),
        jobs=jobs,
        freshest_job=jobs[0] if jobs else None,
    )


def normalize_domain(domain: str | None) -> str | None:
    if domain is None or not domain.strip():
        return None
    value = domain.strip()
    parsed = urlsplit(value if "://" in value else f"//{value}")
    hostname = parsed.hostname
    if hostname is None:
        return None
    normalized = hostname.casefold().rstrip(".")
    return normalized[4:] if normalized.startswith("www.") else normalized


def _group_domains(companies: list[Company]) -> set[str]:
    return {
        domain
        for company in companies
        if (domain := normalize_domain(company.domain)) is not None
    }


def _ensure_name_fallback_is_unambiguous(
    groups: dict[int, list[Company]],
    target_names: set[str],
) -> None:
    matching_domains = {
        domain
        for members in groups.values()
        if any(member.normalized_name in target_names for member in members)
        for domain in _group_domains(members)
    }
    if len(matching_domains) > 1:
        raise CompanyCanonicalizationAmbiguityError(
            "Exact normalized-name fallback matches conflicting domains"
        )


def _resolve_root_id(
    company: Company,
    companies_by_id: dict[int, Company],
) -> int:
    current = company
    visited: set[int] = set()
    while current.canonical_company_id is not None:
        if current.id in visited:
            raise CompanyCanonicalizationError("Canonical company membership is cyclic")
        visited.add(current.id)
        parent = companies_by_id.get(current.canonical_company_id)
        if parent is None:
            raise CompanyCanonicalizationError(
                "Canonical company membership references a missing company"
            )
        current = parent
    return current.id
