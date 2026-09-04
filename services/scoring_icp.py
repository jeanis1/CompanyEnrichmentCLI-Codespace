from dataclasses import dataclass

from models.company import Company
from models.icp import ICPScore


@dataclass(frozen=True)
class ICPProfile:
    min_employee_count: int = 1000
    target_industries: frozenset[str] = frozenset(
        {"Software", "SaaS", "Technology", "Internet"}
    )
    target_country: str = "United States"
    min_annual_revenue: float = 10_000_000
    qualification_threshold: int = 70


DEFAULT_ICP_PROFILE = ICPProfile()


def score_company(
    company: Company,
    profile: ICPProfile = DEFAULT_ICP_PROFILE,
) -> ICPScore:
    employee_score = (
        30
        if company.employee_count is not None
        and company.employee_count >= profile.min_employee_count
        else 0
    )

    industry_score = 30 if company.industry in profile.target_industries else 0

    geography_score = (
        20 if company.location.country == profile.target_country else 0
    )

    revenue_score = (
        20
        if company.annual_revenue is not None
        and company.annual_revenue >= profile.min_annual_revenue
        else 0
    )

    total_score = (
        employee_score
        + industry_score
        + geography_score
        + revenue_score
    )

    return ICPScore(
        score=total_score,
        employee_score=employee_score,
        industry_score=industry_score,
        geography_score=geography_score,
        revenue_score=revenue_score,
        is_qualified=total_score >= profile.qualification_threshold,
    )
