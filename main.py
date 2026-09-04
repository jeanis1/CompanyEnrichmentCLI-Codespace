import argparse
import sys

from pydantic import ValidationError

from clients.abstract_api import AbstractAPIClient, AbstractAPIError
from config import ConfigurationError, Settings
from services.company_enrichment import enrich_company
from services.persistence import save_results_csv, save_results_json
from services.scoring_icp import score_company


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enrich a company using its domain."
    )
    parser.add_argument(
        "domain",
        help="Domain to process, e.g. example.com",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    domain = args.domain.strip().lower()

    try:
        settings = Settings.from_env()
        client = AbstractAPIClient(
            api_key=settings.abstract_api_key,
            base_url=settings.abstract_api_url,
            timeout_seconds=settings.request_timeout_seconds,
            max_retries=settings.max_retries,
            backoff_seconds=settings.backoff_seconds,
        )

        company = enrich_company(domain, client)
        icp_score = score_company(company)

        json_path = save_results_json(
            company,
            icp_score,
            filename=f"{company.domain}.json",
            output_dir=settings.output_dir,
        )
        csv_path = save_results_csv(
            company,
            icp_score,
            output_dir=settings.output_dir,
        )

    except (ConfigurationError, AbstractAPIError, ValidationError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\n--- Normalized Company ---")
    print(company.model_dump_json(indent=2))

    print("\n--- ICP Score ---")
    print(icp_score.model_dump_json(indent=2))

    print("\nResults persisted:")
    print(f"- {json_path}")
    print(f"- {csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
