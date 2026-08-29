import argparse 

from clients.abstract_api import get_company_by_domain

parser = argparse.ArgumentParser(
    description="Enrich a company using its domain."
)

parser.add_argument("domain",
                     help="Domain to process, e.g. example.com"
)

args = parser.parse_args()


print(f"Domain: {args.domain}")

company_data = get_company_by_domain(
    args.domain, 
    inspect_response=True,
)