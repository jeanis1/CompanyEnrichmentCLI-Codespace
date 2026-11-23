import logging
import os

from functools import partial
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from services.batch_processing import (
    skip_recently_enriched,
    remove_input_duplication,
    validate_input,
    BatchProcessingError,
    enrich_batch,
)
from config import Settings
from database.database import get_connection
from clients.apollo_api import request_company_by_domain_apollo
from services.domains import normalize_domain
from database import repository

settings = Settings.from_env()
app = FastAPI()
API_KEY = os.getenv("API_KEY")
log = logging.getLogger("ingest")

DEFAULT_MAX_CALLS = 100


POSTED_TO_APOLLO = {
    "name": "name",
    "industry": "industry",
    "employee_count": "estimated_num_employees",
    "annual_revenue": "annual_revenue",
    "year_founded": "year_founded",
    "company_type": "type",
    "description": "description",
    "linkedin_url": "linkedin_url",
    "city": "city",
    "state": "state",
    "country": "country",
}


class CompanyIn(BaseModel):
    row_number: int
    name: str
    domain: str
    industry: str = ""
    employee_count: int | str | None = None
    annual_revenue: float | str | None = None
    year_founded: int | str | None = None
    city: str = ""
    state: str = ""
    country: str = ""
    company_type: str = ""
    description: str = ""
    linkedin_url: str = ""
    enrichment_source: str = ""


class CompanyResult(BaseModel):
    row_number: int
    status: str  # SUCCESS | FAIL | SKIPPED
    icp_score: float | None = None
    is_qualified: bool | None = None
    error_type: str | None = None


def _filled(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None and v != ""}


def _empty(v) -> bool:
    return v is None or v == ""


def initialize_batch_from_rows(rows: list[CompanyIn]) -> list[dict]:
    batch = []

    for row in rows:
        entry = {
            "row_number": row.row_number,
            "domain": row.domain,
            "source": row.enrichment_source,
            "status": None,
            "icp_score": None,
            "is_qualified": None,
            "error_type": None,
            "error_message": None,
        }

        entry.update(_filled(row.model_dump()))
        batch.append(entry)
    return batch


def merge_posted_into_raw(raw: dict, posted: dict) -> dict:
    merged = dict(raw.get("organization"))
    for field, key in POSTED_TO_APOLLO.items():
        if _empty(merged.get(key)) and not _empty(posted.get(field)):
            merged[key] = posted[field]
    return {**raw, "organization": merged}


def get_missing_icp_and_qualification(raw: list[dict], conn) -> list[dict]:
    # 1 Get missing ICP scores
    missing_icp = []
    for row in raw:
        if row["icp_score"] is None or row["icp_score"] == "":
            missing_icp.append(row)
    for row in missing_icp:
        row["icp_score"] = repository.get_company_icp_score(
            conn, normalize_domain(row["domain"])
        )

    # 2 Get missing qualification_results
    missing_qualification = []
    for row in raw:
        if row["is_qualified"] is None or row["is_qualified"] == "":
            missing_qualification.append(row)
    for row in missing_qualification:
        row["is_qualified"] = repository.get_company_qualification_result(
            conn, normalize_domain(row["domain"])
        )

    return raw


def fetch_with_posted(
    domain: str, *, posted_by_domain: dict, api_key: str
) -> dict:
    raw = request_company_by_domain_apollo(domain, api_key=api_key)
    return merge_posted_into_raw(raw, posted_by_domain.get(domain, {}))


def get_db():
    conn = get_connection(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()


@app.post("/companies", response_model=list[CompanyResult])
def score(rows: list[CompanyIn], conn=Depends(get_db)) -> list[dict]:
    try:
        batch = initialize_batch_from_rows(rows)
        batch = validate_input(batch)
        batch = remove_input_duplication(batch)
        batch = skip_recently_enriched(conn, batch)
    except BatchProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    posted_by_domain = {r.domain: r.model_dump() for r in rows}
    fetch_company = partial(
        fetch_with_posted,
        posted_by_domain=posted_by_domain,
        api_key=settings.apollo_api_key,
        conn=conn,
    )
    batch = enrich_batch(
        conn, batch, fetch_company, settings.output_dir, DEFAULT_MAX_CALLS
    )
    batch = get_missing_icp_and_qualification(batch, conn)

    # Return the icp_score & qualification result back as Response body
    return [
        {
            "row_number": e["row_number"],
            "status": e["status"],
            "icp_score": e.get("icp_score"),
            "is_qualified": e.get("is_qualified"),
            "error_type": e.get("error_type"),
        }
        for e in batch
    ]
