from collections.abc import Callable
from models.company import Company, CompanyLocation

class CompanyEnrichmentError(Exception): 
    pass

CompanyFetcher = Callable[[str], dict]

def enrich_company(
        domain: str,
        fetch_company: CompanyFetcher,
) -> Company:

    raw = fetch_company(domain)

    if not raw.get("name"):
        raise CompanyEnrichmentError(
            f"No usable company data found for domain: {domain}"
        )    

    return Company(
        name = raw.get("name"),
        domain = raw.get("domain"),
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
