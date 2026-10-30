import pytest
import os
import psycopg

from dotenv import load_dotenv
from pathlib import Path
from models.company import Company, CompanyLocation
from models.icp import ICPScore

load_dotenv()


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
            city="San Francisco", state="California", country="United States"
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


@pytest.fixture
def conn():
    # Real PostgreSQL connection toa throaway test database. Never DATABASE_URL
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(Path("database/schema.sql").read_text())
        conn.execute(
            "TRUNCATE qualification_results, enrichment_runs, companies "
            "RESTART IDENTITY CASCADE"
        )
        yield conn


@pytest.fixture
def apollo_payload():
    return {
        "organization": {
            "name": "OpenAI",
            "industry": "Technology",
            "estimated_num_employees": 1500,
            "annual_revenue": 20_000_000,
            "city": "San Francisco",
            "state": "California",
            "country": "United States",
        }
    }
