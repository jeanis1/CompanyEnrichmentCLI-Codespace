from models.company import Company
from models.icp import ICPProfile
from services.scoring_icp import score_company

def test_qualified_company_gets_full_score(
    qualified_company,
):
    result = score_company(
        qualified_company   
    )

    assert result.score == 100 
    assert result.employee_score == 30
    assert result.industry_score == 30
    assert result.geography_score == 20
    assert result.revenue_score == 20
    assert result.is_qualified is True

def test_company_with_no_matching_criteria_gets_zero():
    company = Company(
        name = "Small Company",
        domain = "smallcompany.com",
        industry= "Retail",
        employee_count=10,
        annual_revenue=500_000,
    )

    result = score_company(company)

    assert result.score == 0
    assert result.is_qualified is False

def test_company_at_qualification_threshold_is_qualified():
    company = Company(
        name="Threshold Company",
        domain="threshold.com",
        industry="Technology",
        employee_count=1000,
        annual_revenue=None,
        location={
            "country": "United States",
        },
    )
    result = score_company(company) 

    assert result.score == 80
    assert result.is_qualified is True
    

def test_missing_optional_data_does_not_crash():
    company = Company (
        name = "Unknown Company",
        domain = "unknown.com",
    )

    result = score_company(company)

    assert result.score == 0
    assert result.is_qualified is False

def test_custom_icp_profile_changes_scoring():
    company = Company(
        name="Startup",
        domain="startup.com",
        industry="Technology",
        employee_count=100,
        annual_revenue=2_000_000,
        location={
            "country": "United States",
        },
    )

    startup_icp = ICPProfile(
        minimum_employees=50,
        minimum_revenue=1_000_000,
        qualification_score=70,
        indusries=frozenset({
            "Technology",
        })
        countries=frozenset({
            "United States"
        }),
    )

    result = score_company(
        company,
        startup_icp,
    )

    assert result.score == 100
    assert result.is_qualified is True
