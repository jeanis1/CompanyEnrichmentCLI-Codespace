from collections.abc import Callable
from models.company import Company, CompanyLocation

class CompanyEnrichmentError(Exception): 
    pass

CompanyFetcher = Callable[[str], dict]


def enrich_company_abstract(
        domain: str,
        fetch_company: CompanyFetcher,
) -> Company:

    raw = fetch_company(domain)
    return normalize_abstract_api(raw)

def normalize_abstract_api(raw:dict) -> Company : 
    if not raw.get("name"):
        raise CompanyEnrichmentError("No usable AbstractAPI company data.")


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


def enrich_company_apollo(
        domain: str, 
        fetch_company: CompanyFetcher,
) -> Company:

    raw = fetch_company(domain)
    return normalize_apollo_api(raw, domain)


def normalize_apollo_api(
        raw:dict,
        requested_domain: str
    ) -> Company : 
    
    organization = raw.get("organization")

    if not organization or not organization.get("name"):
        raise CompanyEnrichmentError("No usable Apollo company data.")

    return Company(
    name = organization.get("name"),
    domain = requested_domain,
    industry=organization.get("industry"),
    employee_count=organization.get("employees_count"),
    annual_revenue=organization.get("annual_revenue"),
    year_founded=organization.get("year_founded"),
    company_type=organization.get("type"),
    description=organization.get("description"),
    linkedin_url=organization.get("linkedin_url"),
    location=CompanyLocation(
        city=organization.get("locality"),
        state=organization.get("state"),
        country=organization.get("country"),
    ),

    enrichment_source="apollo",
    )