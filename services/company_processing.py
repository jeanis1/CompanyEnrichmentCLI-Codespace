import logging

import psycopg
from pydantic import ValidationError

from clients.apollo_api import ApolloAPIError
from database import repository
from services.company_enrichment import (
    CompanyEnrichmentError,
    enrich_company_apollo,
)
from services.persistence import persist_company_result
from services.scoring_icp import score_company
from services.domains import normalize_domain

logger = logging.getLogger(__name__)


def process_company(conn, domain, fetch_company):
    domain = normalize_domain(
        domain
    )  # ValueError for invalid input then no run created
    run_id = repository.start_enrichment_run(conn, domain)
    try:
        company = enrich_company_apollo(domain, fetch_company)
        icp_score = score_company(company)
        persist_company_result(conn, run_id, company, icp_score)  # one transaction
    except Exception as exc:
        _record_failure(conn, run_id, exc)
        raise
    return company, icp_score


def _record_failure(conn, run_id, exc):
    try:
        repository.fail_enrichment_run(conn, run_id, error_code_for(exc))
    except (psycopg.Error, ValueError):
        # DB not available, or commit already succeeded. fail_stale_runs() handles leftover procesisng
        logger.exception("Could not record failure for run_id%=s", run_id)


def error_code_for(exc) -> str:
    # not stored
    if isinstance(exc, ApolloAPIError):
        return f"provider_{exc.code}"
    if isinstance(exc, (CompanyEnrichmentError, ValidationError)):
        return "invalid_company_data"
    if isinstance(exc, psycopg.IntegrityError):
        return "database_constraint"
    if isinstance(exc, psycopg.Error):
        return "database_error"
    return "unexpected_error"
