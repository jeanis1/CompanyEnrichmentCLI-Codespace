from models.company import Company
from models.icp import ICPScore

def score_company(company: Company) -> ICPScore:

    employee_score = 0 
    industry_score = 0 
    geography_score = 0
    revenue_score = 0

    #Employee fit
    if company.employee_count is not None:
        if company.employee_count >= 1000:
            employee_score = 30

    #Industry fit
    if company.industry:
        target_industries = { 
            "Software",
            "SaaS",
            "Technology",
            "Internet",
        }

        if company.industry in target_industries:
            industry_score = 30

    #Geography fit 
    if company.location.country == "United States":
        geography_score = 20

    #Revenue fit
    if (
        company.annual_revenue is not None
        and company.annual_revenue >= 10_000_000
    ):
        revenue_score = 20

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
        is_qualified=total_score >= 70,
    )

        