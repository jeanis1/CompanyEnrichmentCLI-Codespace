from models.company import Company
from models.icp import ICPScore, ICPProfile

DEFAULT_ICP = ICPProfile()


def score_company(
    company: Company,
    profile: ICPProfile = DEFAULT_ICP,
) -> ICPScore:
    
    employee_score = 0 
    industry_score = 0 
    geography_score = 0
    revenue_score = 0

    #Employee fit
    if ( 
    company.employee_count is not None
        and company.employee_count >= profile.minimum_employees
        ):
            employee_score = 30

    #Industry fit
    if company.industry in profile.industries:
            industry_score = 30

    #Geography fit 
    if company.location.country in profile.countries:
        geography_score = 20

    #Revenue fit
    if (
        company.annual_revenue is not None
        and company.annual_revenue >= profile.minimum_revenue
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
        is_qualified=total_score >= profile.qualification_score,
    )

        