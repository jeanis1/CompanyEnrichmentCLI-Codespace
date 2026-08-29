from clients.abstract_api import get_company_by_domain
from models.company import Company, CompanyLocation

def enrich_company(domain: str) -> Company:

    raw = get_company_by_domain(domain)
    
    company = Company(
        name = raw.get("name"),
        domain = raw.get("domain"),
        

        industry=raw.get("industry"),
        employee_count=raw.get("employees_count"),
        annual_revenue=raw.get("annual_revenue"),
        year_founded=raw.get("year_founded"),

        company_type=raw.get("type"),
        deedescription=raw.get("description"),

        linkedin_url=raw.get("linkedin_url"),

        location=CompanyLocation(
            city=raw.get("locality"),
            state=raw.get("state"),
            country=raw.get("country"),
        ),

        enrichment_source="abstract_api",
    )
    return company