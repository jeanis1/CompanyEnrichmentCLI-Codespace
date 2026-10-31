import argparse
import sys
from functools import partial

import psycopg

from clients.apollo_api import ApolloAPIError, get_company_by_domain_apollo
from config import Settings
from database import repository
from database.database import get_connection
from database.init_db import create_tables
from services.batch_processing import (
    BatchProcessingError,
    initialize_batch_processing,
    order_and_rank_batch,
    output_summary,
    remove_database_duplication,
    remove_input_duplication,
    save_batch_summary,
    validate_input,
)
from services.company_enrichment import CompanyEnrichmentError, enrich_company_apollo
from services.company_processing import process_company
from services.persistence import (
    company_to_row,
    persist_company_result,
    save_output_files,
)
from services.scoring_icp import score_company
from pydantic import ValidationError


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

    return parser.parse_args()


def process_single_domain(conn, domain: str, settings: Settings) -> int:
    fetch_company = partial(
        get_company_by_domain_apollo,
        api_key=settings.apollo_api_key,
    )
    try:
        company, icp_score = process_company(conn, domain, fetch_company)
    except (ApolloAPIError, CompanyEnrichmentError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValidationError:
        # checked before ValueError(parent) as message can contain provider data
        print("Error: Provider returned invalid company data.", file=sys.stderr)
        return 1
    except ValueError as exc: #Invalid data
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


def process_batch(conn, csv_path: str, settings: Settings) -> int:
    try:
        batch = initialize_batch_processing(csv_path)
        batch = validate_input(batch)
        batch = remove_input_duplication(batch)
        batch = remove_database_duplication(batch)

    except BatchProcessingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if settings is None:
        print("Settings must be configured.")
        conn.close()
        return

    fetch_company = partial(
        get_company_by_domain_apollo,
        api_key=settings.apollo_api_key,
    )

    for entry in batch:
        if entry["status"] == "FAIL":
            continue
        try:
            company, icp_score = process_company(conn, entry["domain"], fetch_company)
        except Exception as exc:
            entry.update(status="FAIL", error_type=type(exc).__name__)
            continue
        entry.update(
            status="SUCCESS",
            icp_score=icp_score.score,
            qualification=icp_score.is_qualified,
        )
        save_output_files(company, icp_score, settings.output_dir)

    batch = order_and_rank_batch(batch)
    save_batch_summary(batch)
    output_summary(batch)

    return 1 if any(entry["status"] == "FAIL" for entry in batch) else 0


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()

    with get_connection(settings.database_url) as conn:
        create_tables(conn)
        if args.csv or args.domain:
            repository.fail_stale_runs(
                conn
            )  # Close out runs left 'running' in DB by previous crash

        if args.csv:
            return process_batch(conn, args.csv, settings)

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
