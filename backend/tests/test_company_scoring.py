from dataclasses import dataclass

from backend.models.company import Company
from backend.research.company_scoring import (
    CompanyScoreInput,
    build_company_score_input,
    score_company,
)


@dataclass(frozen=True)
class FakeJob:
    title: str
    active: bool
    function: str | None = None
    location: str | None = None


def company_input(
    *,
    names: tuple[str, ...] = (),
    stages: tuple[str, ...] = (),
    locations: tuple[str, ...] = (),
    descriptions: tuple[str, ...] = (),
    categories: tuple[str, ...] = (),
) -> CompanyScoreInput:
    return CompanyScoreInput(
        names=names,
        stages=stages,
        locations=locations,
        descriptions=descriptions,
        categories=categories,
    )


def test_active_engineering_outweighs_max_non_hiring_bonuses() -> None:
    engineering = score_company(
        company_input(),
        [FakeJob(title="Software Engineer", active=True)],
    )
    max_non_hiring = score_company(
        company_input(
            stages=("Series G",),
            locations=("San Francisco",),
            descriptions=("Software AI machine learning data cloud infrastructure",),
        ),
        [],
    )

    assert engineering.score == 50
    assert max_non_hiring.score == 40
    assert engineering.score > max_non_hiring.score


def test_inactive_jobs_are_ignored() -> None:
    result = score_company(
        company_input(),
        [
            FakeJob(
                title="Junior AI Engineer Internship",
                active=False,
                location="Remote",
            )
        ],
    )

    assert result.score == 0
    assert result.reasons == ()


def test_active_early_career_job_scores_once() -> None:
    result = score_company(
        company_input(),
        [
            FakeJob(title="Operations Intern", active=True),
            FakeJob(title="Junior Chief of Staff", active=True),
        ],
    )

    assert result.score == 20
    assert result.reasons[0].code == "active_early_career_jobs"
    assert result.reasons[0].points == 20


def test_series_a_through_g_and_post_ipo_score_but_seed_unknown_do_not() -> None:
    assert score_company(company_input(stages=("Series A",)), []).score == 10
    assert score_company(company_input(stages=("series g",)), []).score == 10
    assert score_company(company_input(stages=("Post-IPO",)), []).score == 10
    assert score_company(company_input(stages=("Seed",)), []).score == 0
    assert score_company(company_input(stages=("Pre-Seed",)), []).score == 0
    assert score_company(company_input(stages=("Unknown",)), []).score == 0


def test_company_or_active_job_sf_bay_area_remote_location_scores() -> None:
    company_location = score_company(
        company_input(locations=("San Francisco Bay Area",)),
        [],
    )
    job_location = score_company(
        company_input(),
        [FakeJob(title="Designer", active=True, location="Remote - US")],
    )

    assert company_location.score == 10
    assert job_location.score == 10
    assert company_location.reasons[0].code == "target_location"
    assert job_location.reasons[0].code == "target_location"


def test_technical_groups_are_distinct_capped_and_avoid_substring_matches() -> None:
    all_groups = score_company(
        company_input(
            names=("Software Works",),
            descriptions=("Artificial intelligence and data systems",),
            categories=("Cloud Infrastructure", "ML"),
        ),
        [],
    )
    false_substrings = score_company(
        company_input(
            names=("Retailer",),
            descriptions=("A database of sailboats",),
            categories=("Claims",),
        ),
        [],
    )

    assert all_groups.score == 20
    assert all_groups.reasons[0].evidence == (
        "software",
        "ai_ml",
        "data",
        "infra_cloud",
    )
    assert false_substrings.score == 0


def test_missing_fields_are_safe() -> None:
    result = score_company(company_input(), [FakeJob(title="", active=True)])

    assert result.score == 0
    assert result.reasons == ()


def test_job_order_does_not_change_score_or_reason_order() -> None:
    company = company_input(
        stages=("Series B",),
        locations=("Remote",),
        categories=("Software",),
    )
    jobs = [
        FakeJob(title="Backend Engineer", active=True),
        FakeJob(title="Engineering Intern", active=True),
        FakeJob(title="Platform Engineer", active=True),
    ]

    forward = score_company(company, jobs)
    reversed_result = score_company(company, reversed(jobs))

    assert forward == reversed_result
    assert [reason.code for reason in forward.reasons] == [
        "active_engineering_jobs",
        "active_early_career_jobs",
        "growth_stage",
        "target_location",
        "technical_groups",
    ]
    assert forward.reasons[0].points == 60


def test_aggregate_input_includes_richer_non_root_facts_without_mutation() -> None:
    root = Company(
        id=1,
        name="Acme",
        normalized_name="acme",
        source="speedrun",
        source_metadata={"industries": []},
    )
    member_metadata = {
        "categories": ["AI", "Developer Tools"],
        "industries": ["Cloud"],
        "ignored": ["not included"],
    }
    member = Company(
        id=2,
        canonical_company_id=1,
        name="Acme Technologies",
        normalized_name="acme technologies",
        source="topstartups",
        stage="Series A",
        location="San Francisco",
        description="Machine learning infrastructure",
        source_metadata=member_metadata,
    )
    original_root_metadata = {"industries": []}
    original_member_metadata = {
        key: list(value) for key, value in member_metadata.items()
    }

    result = build_company_score_input([root, member])

    assert result.names == ("Acme", "Acme Technologies")
    assert result.stages == ("Series A",)
    assert result.locations == ("San Francisco",)
    assert result.descriptions == ("Machine learning infrastructure",)
    assert result.categories == ("AI", "Cloud", "Developer Tools")
    assert root.source_metadata == original_root_metadata
    assert member.source_metadata == original_member_metadata


def test_scoring_does_not_mutate_inputs() -> None:
    company = company_input(
        names=("AI Software",),
        stages=("Series C",),
        locations=("Remote",),
    )
    jobs = (
        FakeJob(title="Junior Software Engineer", active=True),
        FakeJob(title="Sales", active=False),
    )

    before_company = company
    before_jobs = jobs
    score_company(company, jobs)

    assert company == before_company
    assert jobs == before_jobs
