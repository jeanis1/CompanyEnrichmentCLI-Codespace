import argparse
import sys
from functools import partial

import psycopg

from clients.apollo_api import ApolloAPIError, request_company_by_domain_apollo
from config import Settings
from database import repository
from fastapi import Depends
from database.database import get_connection
from services.batch_processing import (
    BatchProcessingError,
    initialize_batch_processing,
    order_and_rank_batch,
    output_summary,
    skip_recently_enriched,
    remove_input_duplication,
    save_batch_summary,
    validate_input,
    enrich_batch,
)
from services.company_enrichment import CompanyEnrichmentError
from services.company_processing import enrich_score_qualify
from services.persistence import save_output_files
from pydantic import ValidationError

# Provider errors that suggest apollo is strugging (not this one domain)
TRANSIENT_PROVIDER_CODES = {"rate_limited", "server_error", "timeout", "connection"}
MAX_CONSECUTIVE_PROVIDER_FAILURES = 5
DEFAULT_MAX_CALLS = 100

settings = Settings.from_env()


def get_db():
    conn = get_connection(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Enrich a company using its domain",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--domain",
        help="Single domain to process, e.g. stripe.com",
    )

    DEFAULT_BATCH_CSV = "./data/input/batch_company.csv"
    group.add_argument(
        "--csv",
        nargs="?",
        const=DEFAULT_BATCH_CSV,
        help=f"CSV file containing domains to process (default : {DEFAULT_BATCH_CSV})",
    )

    group.add_argument(
        "--query",
        choices=[
            "get-top-icp-score",
            "get-total-count-industry",
            "get-list-enrichment-fail",
            "get-duplicate-domains",
            "get-qualified-from-all",
            "get-qualified-from-batch",
            "get-processed-this-week",
        ],
        metavar="QUERY",
        help="Queries Available:\n"
        " get-top-icp-score\n"
        " get-total-count-industry\n"
        " get-list-enrichment-fail\n"
        " get-duplicate-domains\n"
        " get-qualified-from-all\n"
        " get-qualified-from-batch\n"
        " get-processed-this-week",
    )

    group.add_argument(
        "--get-specific-industry",
        type=str,
        metavar="INDUSTRY_NAME",
        help="Get companies in specific industry.",
    )

    parser.add_argument(
        "--max-calls",
        type=int,
        default=DEFAULT_MAX_CALLS,
        help=f"Maximum Apollo calls per batch run (default: {DEFAULT_MAX_CALLS})",
    )

    return parser.parse_args()


def process_single_domain(conn, domain: str, settings: Settings) -> int:
    fetch_company = partial(
        request_company_by_domain_apollo,
        api_key=settings.apollo_api_key,
    )

    try:
        company, icp_score = enrich_score_qualify(conn, domain, fetch_company)

    except (ApolloAPIError, CompanyEnrichmentError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except ValidationError:
        # checked before ValueError(parent) as message can contain provider data
        print("Error: Provider returned invalid company data.", file=sys.stderr)
        return 1

    except ValueError as exc:  # Invalid data
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except psycopg.Error as exc:
        print(
            f"Database persistence failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1

    save_output_files(company, icp_score, settings.output_dir)
    return 0


def process_batch(
    conn, csv_path: str, settings: Settings, max_calls: int = DEFAULT_MAX_CALLS
) -> int:
    try:
        batch = initialize_batch_processing(csv_path)
        batch = validate_input(batch)
        batch = remove_input_duplication(batch)

    except BatchProcessingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if settings is None:
        print("Settings must be configured.")
        conn.close()
        return

    batch = skip_recently_enriched(conn, batch)

    fetch_company = partial(
        request_company_by_domain_apollo,
        api_key=settings.apollo_api_key,
    )
    batch = enrich_batch(conn, batch, fetch_company, settings.output_dir, max_calls)

    batch = order_and_rank_batch(batch)
    save_batch_summary(batch)
    output_summary(batch)

    return 1 if any(entry["status"] == "FAIL" for entry in batch) else 0


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()

    with get_connection(settings.database_url) as conn:
        if args.csv or args.domain:
            repository.fail_stale_runs(  # Close runs left 'running' in DB by previous crash
                conn
            )

        if args.csv:
            return process_batch(conn, args.csv, settings, args.max_calls)

        if args.domain:
            return process_single_domain(conn, args.domain, settings)

        if args.get_specific_industry:
            results = repository.get_industry_count(conn, args.get_specific_industry)
            for row in results:
                print(row)
            return

        match args.query:
            case "get-specific-industry":
                select_industry_list = repository.get_industry_count(
                    conn, "Computer software"
                )
                for row in select_industry_list:
                    print(row)

            case "get-top-icp-score":
                icp_list = repository.get_highest_icp_score(conn)
                for row in icp_list:
                    print(row)

            case "get-total-count-industry":
                industry_total_list = repository.get_total_industry_count(conn)
                for row in industry_total_list:
                    print(row)

            case "get-list-enrichment-fail":
                failed_list = repository.get_failed_runs(conn)
                for row in failed_list:
                    print(row)

            case "get-duplicate-domains":
                duplicate_list = repository.get_duplicate(conn)
                print(duplicate_list)

            case "get-qualified-from-all":
                total_qualified_list = repository.get_total_qualfication(conn)
                print(f"{total_qualified_list}%")

            case "get-qualified-from-batch":
                batch_qualified_list = repository.get_batch_qualification(conn)
                print(batch_qualified_list)

            case "get-processed-this-week":
                processed_this_week_list = repository.get_processed_this_week(conn)
                print(processed_this_week_list)


# Entry-point validation
if __name__ == "__main__":
    raise SystemExit(main())
