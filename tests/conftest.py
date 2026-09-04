import pytest

from models.company import Company, CompanyLocation
from models.icp import ICPScore

@pytest.fixture 
def qualified_company() -> Company:
    return Company(
        name="OpenAI",
        domain="openai.com",
        industry="Technology",
        employee_count=1500,
        annual_revenue=20_000_000,
        year_founded=2015,
        location=CompanyLocation(
            city="San Francisco",
            state="California",
            country="United States"
        ),
        enrichment_source="abstract_api",
    )

@pytest.fixture
def qualified_score() -> ICPScore:
    return ICPScore(
        score=100, 
        employee_score=30,
        industry_score=30,
        geography_score=20, 
        revenue_score=20,
        is_qualified=True,
    )