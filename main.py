import argparse 
import sys
from functools import partial

from clients.abstract_api import AbstractAPIError, get_company_by_domain
from config import Settings
from services.company_enrichment import enrich_company
from services.persistence import save_results_json, save_results_csv
from services.scoring_icp import score_company


def parse_args():
    parser = argparse.ArgumentParser(
        description="Enrich. a company using its domain"
    )

    parser.add_argument(
        "domain",
        help="Domain to process, e.g. example.com",
    )

    return parser.parse_args()

def main() -> int:
    args = parse_args()

    try:
        settings = Settings.from_env()

        fetch_company = partial( 
            get_company_by_domain,
            api_key=settings.abstract_api_key,
        )

        company = enrich_company(
            args.domain,
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

# Entry-point validation
if __name__ == "__main__":
    raise SystemExit(main())

