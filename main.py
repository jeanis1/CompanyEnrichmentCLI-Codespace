import argparse 

from services.company_enrichment import enrich_company
from services.scoring_icp import score_company
from services.persistence import save_results_json, save_results_csv


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

save_results_json(
    company, 
    icp_score,
    filename=f"{company.domain}.json",
)

save_results_csv(
    company,
    icp_score,
)

print("\nResults persisted to output/")