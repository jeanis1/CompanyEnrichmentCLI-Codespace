from dataclasses import dataclass

from pydantic import BaseModel

# Scoring Rules
@dataclass (frozen=True)
class ICPProfile:
    minimum_employees: int = 1000
    minimum_revenue: float = 10_000_000
    qualification_score: int = 70

    industries: frozenset[str] = frozenset({
        "Software",
        "SaaS",
        "Technology", 
        "Internet",
    })

    countries: frozenset[str] = frozenset({
        "United States", 
    })

# Scoring Result
class ICPScore(BaseModel):
    score: int
    employee_score: int
    industry_score: int
    geography_score: int
    revenue_score: int
    is_qualified: bool

