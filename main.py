import argparse 

from services.company_enrichment import enrich_company
from services.scoring_icp import score_company

parser = argparse.ArgumentParser(
    description="Enrich a company using its domain."
)

parser.add_argument("domain",
                     help="Domain to process, e.g. example.com"
)

args = parser.parse_args()

company = enrich_company(args.domain)

print("\n--- Normalized Company ---")
print(company.model_dump_json(indent=2))

icp_score = score_company(company)

print("\n---ICP Score ---")
print(icp_score.model_dump_json(indent=2))
