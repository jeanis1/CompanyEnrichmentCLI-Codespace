import argparse 
import sys

from functools import partial
from clients.abstract_api import AbstractAPIError, get_company_by_domain
from config import Settings
from services.company_enrichment import enrich_company
from services.persistence import save_results_json, save_results_csv
from services.scoring_icp import score_company
from services.batch_processing import BatchProcessingError, initialize_batch_processing, remove_database_duplication,remove_input_duplication, validate_domain_input, build_list   


def parse_args():
    parser = argparse.ArgumentParser(
        description="Enrich. a company using its domain"
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--domain",
        help="Single domain to process, e.g. stripe.com",
    )

    group.add_argument(
        "--csv",
        help="CSV file containing domains to process",
    )

    return parser.parse_args()

def process_single_domain(domain: str) -> int:
    try:
        settings = Settings.from_env()

        fetch_company = partial( 
            get_company_by_domain,
            api_key=settings.abstract_api_key,
        )

        company = enrich_company(
            domain,
            fetch_company,
        )

        icp_score = score_company(company)

        print(company.model_dump_json(indent=2))
        print(icp_score.model_dump_json(indent=2))

        save_results_json(
            company, 
            icp_score,
            filename=f"{company.domain}.json",
            output_dir=settings.output_dir
        )

        save_results_csv(
            company,
            icp_score,
            output_dir=settings.output_dir,
            )

        return 0 
    
    except AbstractAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1 


def process_batch(csv_path:str) -> int: 
    try:
        initial_batch = initialize_batch_processing(csv_path)
        basic_validated_batch = validate_domain_input(initial_batch)
        deduplicated_batch = remove_input_duplication(basic_validated_batch)
        processed_batch = remove_database_duplication(deduplicated_batch)
        build_list(processed_batch)
        return 0

    except BatchProcessingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    args = parse_args()
    if args.csv: 
        return process_batch(args.csv)

    return process_single_domain(args.domain)


# Entry-point validation
if __name__ == "__main__":
    raise SystemExit(main())

