from pydantic import BaseModel

class ICPScore(BaseModel):
    score: int
    employee_score: int
    industry_score: int
    geography_score: int
    revenue_score: int
    is_qualified: bool

