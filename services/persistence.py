import csv
import json
from pathlib import Path

from models.company import Company
from models.icp import ICPScore
from database import repository


DEFAULT_OUTPUT_DIR = Path("data/output")

def save_results_json(
    company: Company,
    icp_score : ICPScore,
    filename: str = "result.json",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None: 

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = output_dir / filename

    data = {
        "company": company.model_dump(),
        "icp_score": icp_score.model_dump(),
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(data,file, indent=2)


def save_results_csv(
    company: Company,
    icp_score: ICPScore,
    filename: str = "results.csv",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = output_dir / filename

    row = {
        "name": company.name,
        "domain": company.domain,
        "industry": company.industry, 
        "employee_count": company.employee_count,
        "annual_revenue": company.annual_revenue,
        "year_founded": company.year_founded,
        "city": company.location.city,
        "state": company.location.state,
        "country": company.location.country,
        "company_type": company.company_type,
        "description": company.description,
        "linkedin_url": company.linkedin_url,
        "enrichment_source": company.enrichment_source,

        "icp_score": icp_score.score,
        "employee_score": icp_score.employee_score,
        "industry_score": icp_score.industry_score,
        "geography_score": icp_score.geography_score,
        "revenue_score": icp_score.revenue_score,
        "is_qualified": icp_score.is_qualified,
    }

    file_exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as file: 
        writer = csv.DictWriter(file, fieldnames=row.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

def company_to_row(company: Company, icp_score) -> dict : 
    return { 
            "name": company.name,
            "domain": company.domain,
            "industry": company.industry,
            "employee_count": company.employee_count,
            "annual_revenue": company.annual_revenue,
            "year_founded": company.year_founded,
            "company_type": company.company_type,
            "description": company.description,
            "linkedin_url": company.linkedin_url,
            "city": company.location.city,
            "state": company.location.state,
            "country": company.location.country,
            "enrichment_source": company.enrichment_source,
            "icp_score": icp_score.score,
            "is_qualified": icp_score.is_qualified,
            }
    
def persist_company_result(conn, company, icp_score) -> int:  
    row = company_to_row(company, icp_score)
    
    with conn.transaction():
        company_id = repository.insert_company(conn, row)
        
        enrichment_id = repository.insert_enrichment_run(
            conn, company_id, row
        )
        
        repository.insert_qualification_result(
            conn,
            company_id,
            enrichment_id,
            row["icp_score"],
            row["is_qualified"],
        )
        
        return enrichment_id