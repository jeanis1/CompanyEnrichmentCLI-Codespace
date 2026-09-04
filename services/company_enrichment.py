from typing import Any, Mapping, Protocol

from models.company import Company, CompanyLocation


class CompanyProvider(Protocol):
    def get_company_by_domain(self, domain: str) -> dict:
        ...


def map_company(raw: Mapping[str, Any]) -> Company:
    return Company(
        name=raw.get("name"),
        domain=raw.get("domain"),
        industry=raw.get("industry"),
        employee_count=raw.get("employees_count"),
        annual_revenue=raw.get("annual_revenue"),
        year_founded=raw.get("year_founded"),
        company_type=raw.get("type"),
        description=raw.get("description"),
        linkedin_url=raw.get("linkedin_url"),
        location=CompanyLocation(
            city=raw.get("locality"),
            state=raw.get("state"),
            country=raw.get("country"),
        ),
        enrichment_source="abstract_api",
    )


def enrich_company(domain: str, provider: CompanyProvider) -> Company:
    raw = provider.get_company_by_domain(domain)
    return map_company(raw)
