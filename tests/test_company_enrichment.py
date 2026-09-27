import pytest

from pydantic import ValidationError

from services.company_enrichment import enrich_company_apollo,CompanyEnrichmentError


def test_enrich_company_maps_api_response():
    fake_response = { 
        "organization": {
        "name": "OpenAI",
        "industry": "Technology",
        "estimated_num_employees": 1500,
        "annual_revenue": 20_000_000,
        "founded_year": 2015,
        "type": "Private",
        "short_description": "AI company",
        "linkedin_url": "https://linkedin.com/company/openai",
        "city": "San Francisco",
        "state": "California",
        "country": "United States",
        }

    }

    def fake_fetch_company(domain: str) -> dict:
        return fake_response

    company = enrich_company_apollo(
        "openai.com",
        fake_fetch_company,
    )

    assert company.name == "OpenAI"
    assert company.domain == "openai.com"
    assert company.employee_count == 1500
    assert company.industry == "Technology"

    assert company.location.city == "San Francisco"
    assert company.location.state == "California"
    assert company.location.country == "United States"

    assert company.enrichment_source == "apollo"

def test_missing_apollo_company_data_raises_enrichment_error():
    malformed_response = { 
        "organization" : None,
    }

    def fake_fetch_company(domain: str) -> dict: 
        return malformed_response
    
    with pytest.raises(CompanyEnrichmentError) as exc_info:
        enrich_company_apollo(
            "openai.com",
            fake_fetch_company,
        )
