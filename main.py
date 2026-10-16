import argparse 
import sys

from functools import partial
from clients.apollo_api import ApolloAPIError, get_company_by_domain_apollo
from config import Settings
from services.company_enrichment import enrich_company_apollo, CompanyEnrichmentError
from services.persistence import save_results_json, save_results_csv
from services.scoring_icp import score_company
from services.batch_processing import BatchProcessingError, initialize_batch_processing, remove_database_duplication,remove_input_duplication, validate_input, save_batch_summary, output_summary, order_and_rank_batch
import pandas as pd

from database.init_db import create_tables
from database.database import get_connection
from database import repository 



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

    group.add_argument(
        "--db",
        help="Manually process Company from the database.",
    )

    return parser.parse_args()

def process_single_domain(domain: str, settings : Settings) -> int:
    try:

        #API Call
        fetch_company = partial( 
            get_company_by_domain_apollo,
            api_key=settings.apollo_api_key,
        )

        #Enrichment
        company = enrich_company_apollo(
            domain,
            fetch_company,
        )

        #Scoring
        icp_score = score_company(company)
        
        #Persistence
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
    
    except (ApolloAPIError, CompanyEnrichmentError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1 


def process_batch(csv_path:str, settings: Settings) -> int: 
    try:
        batch = initialize_batch_processing(csv_path)
        batch = validate_input(batch)
        batch = remove_input_duplication(batch)
        batch = remove_database_duplication(batch)
        

    except BatchProcessingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    
    except Exception:
        raise


    fetch_company = partial( 
        get_company_by_domain_apollo,
        api_key=settings.apollo_api_key,
    )

    for entry in batch: 
        domain = entry["domain"]
        if entry["status"] != "FAIL":
            try:
                company = enrich_company_apollo(
                    domain,
                    fetch_company,
                )

                icp_score = score_company(company)

                save_results_json(company, icp_score, 
                filename=f"{company.domain}.json",
                output_dir=Settings.output_dir
                )

                save_results_csv(
                    company,
                    icp_score,
                    output_dir=Settings.output_dir,
                )

                entry["icp_score"] = icp_score.score
                entry["status"] = "SUCCESS"

            except Exception as e:
                entry["status"] = "FAIL"
                entry["error_type"] = type(e).__name__
                entry["error_message"] = str(e)

    batch = order_and_rank_batch(batch) 
    save_batch_summary(batch)
    output_summary(batch)
    return 0


def manual_database_processing(company_name: str,settings: Settings) -> None: 

    company_name = company_name.strip().lower()
    df = pd.read_csv("data/output/results.csv")
    
    match = df[df["name"].str.lower() == company_name]
    if match.empty:
        print(f"Company {company_name} not found.")
        conn.close()
        return
    
    conn = get_connection(settings.database_url)
    
    try:
        row = match.iloc[0]
        company_id = repository.insert_company(conn, row) 
        run_id = repository.insert_enrichment_run(conn,company_id, row)
        repository.insert_qualification_result(
            conn,
            company_id, 
            run_id,
            row["icp_score"],
            row["is_qualified"],
        )

        #Get specific industry from DB - WORKING
        # select_industry_list = repository.get_industry_count(conn, "Computer software")
        # for row in select_industry_list:
        #     print(row)

        # Rank Top ICP Scores - WORKING
        # icp_list = repository.get_highest_icp_score(conn)
        # for row in icp_list:
        #     print(row)

        # Get Total Count of All Industry - WORKING
        # industry_total_list = repository.get_industry_count(conn)
        # for row in industry_total_list:
        #     print(row)

        # Get List of enrichment failed - WORKING
        # failed_list = repository.get_failed(conn)
        # for row in failed_list:
        #     print(row)

        # Get Duplicate Name Domains : Should Return None (due to overwrite instead of creation for duplicate domains)
        # print("Duplicate Items : ")
        # duplicate_list = repository.get_duplicate(conn)
        # print(duplicate_list)
        
        # Get % Qualified from all accounts in DB 
        print("Total Qualified : ")
        total_qualfied_list = repository.get_qualification_results(conn)
        print(f"{total_qualfied_list}%")
        
        conn.commit()

    finally:
        conn.close()



def main() -> int:
    settings = Settings.from_env()
    conn = get_connection(settings.database_url)
    create_tables(conn)

    args = parse_args()
    if args.csv: 
        return process_batch(args.csv, settings)
    if args.db:
        return manual_database_processing(args.db, settings)
    
    return process_single_domain(args.domain, settings)


# Entry-point validation
if __name__ == "__main__":
    raise SystemExit(main())

