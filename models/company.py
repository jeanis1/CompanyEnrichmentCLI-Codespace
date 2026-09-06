from pydantic import BaseModel, Field
from typing import Optional

class CompanyLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str]= None
    country: Optional[str] = None

# Input Data
class Company(BaseModel):
    #Identity
    name: str
    domain: str

    #Firmographic
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    year_founded: Optional[int] = None

    #Geography
    location: CompanyLocation = Field (
        default_factory=CompanyLocation
    )

    #Company characteristics
    company_type: Optional[str] = None
    description: Optional[str] = None

    #Useful GMT URLs
    linkedin_url: Optional[str] = None

    #Data provenance
    enrichment_source: Optional[str] = None
    