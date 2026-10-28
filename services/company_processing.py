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

logger = logging.getLogger(__name__)

def process_company(conn, domain, fetch_company):
    domain = domain.strip().lower()
    run_id = repository.start_enrichment_run(conn, domain)
    
    try: 
        company = enrich_company_apollo(domain, fetch_company)
        icp_score = score_company(company)
        
    except(
        ApolloAPIError,
        CompanyEnrichmentError,
        ValidationError,
    ) as exc:
        error_code = (
            "provider_error"
            if isinstance(exc, ApolloAPIError)
            else "invalid_company_data"
        )
        
        repository.fail_enrichment_run(conn, run_id, error_code)
        raise
    
    try: 
        persist_company_result(
            conn, 
            run_id,
            company,
            icp_score,
        )
        
    except psycopg.IntegrityError: 
        #Transaction context has already rolled back.
        repository.fail_enrichment_run(
            conn, 
            run_id,
            "database constraint",
        )
        raise
    
    except psycopg.Error:
        # A connection failure during COMMIT can have uncertain outcome.
        # Inspect using a new connection.
        logger.error(
            "Datbase outcome requires inspection for run_id=%s",
            run_id,
        ) 
        raise

    return company, icp_score


