from services.company_enrichment import enrich_company


class FakeCompanyProvider:
    def get_company_by_domain(self, domain: str) -> dict:
        assert domain == "openai.com"
        return {
            "name": "OpenAI",
            "domain": "openai.com",
            "industry": "Technology",
            "employees_count": 1500,
            "annual_revenue": 20_000_000,
            "year_founded": 2015,
            "type": "Private",
            "description": "AI company",
            "linkedin_url": "https://linkedin.com/company/openai",
            "locality": "San Francisco",
            "state": "California",
            "country": "United States",
        }


def test_enrich_company_maps_api_response():
    company = enrich_company("openai.com", FakeCompanyProvider())

    assert company.name == "OpenAI"
    assert company.domain == "openai.com"
    assert company.employee_count == 1500
    assert company.industry == "Technology"
    assert company.location.city == "San Francisco"
    assert company.location.state == "California"
    assert company.location.country == "United States"
    assert company.enrichment_source == "abstract_api"
