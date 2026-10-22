import argparse 
import sys

from functools import partial
from clients.apollo_api import ApolloAPIError, get_company_by_domain_apollo
from config import Settings
from services.company_enrichment import enrich_company_apollo, CompanyEnrichmentError
from services.persistence import save_results_json, save_results_csv, company_to_row
from services.scoring_icp import score_company
from services.batch_processing import BatchProcessingError, initialize_batch_processing, remove_database_duplication,remove_input_duplication, validate_input, save_batch_summary, output_summary, order_and_rank_batch

from database.init_db import create_tables
from database.database import get_connection
from database import repository 



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
            help=f"Queries Available:\n"
                " get-top-icp-score\n"
                " get-total-count-industry\n"
                " get-list-enrichment-fail\n"
                " get-duplicate-domains\n"
                " get-qualified-from-all\n"
                " get-qualified-from-batch\n"
                " get-processed-this-week"
    )
    
    group.add_argument(
        "--get-specific-industry",
        type=str,
        metavar="INDUSTRY_NAME",
        help="Get companies in specific industry."
    )
    
    return parser.parse_args()

def process_single_domain(conn,domain: str, settings : Settings) -> int:
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
        
        #DB
        row = company_to_row(company, icp_score) 
        company_id = repository.insert_company(conn,row)
        enrichment_id = repository.insert_enrichment_run(conn,company_id, row)
        repository.insert_qualification_result(
            conn,
            company_id,
            enrichment_id,
            row["icp_score"],
            row["is_qualified"],
            )
        conn.commit()
        return 0 
    
    except (ApolloAPIError, CompanyEnrichmentError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1 



def process_batch(conn, csv_path:str, settings: Settings) -> int: 
    try:
        batch = initialize_batch_processing(csv_path)
        batch = validate_input(batch)
        batch = remove_input_duplication(batch)
        batch = remove_database_duplication(batch)
        

    except BatchProcessingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


    if settings is None:
        print(f"Settings must be configured.")
        conn.close()
        return    
    
    fetch_company = partial( 
        get_company_by_domain_apollo,
        api_key=settings.apollo_api_key,
    )
    conn = get_connection(settings.database_url)
    
    for entry in batch: 
        domain = entry["domain"]
        if entry["status"] != "FAIL":
            try:
                company = enrich_company_apollo(
                    domain,
                    fetch_company,
                )

                icp_score = score_company(company)
                entry["icp_score"] = icp_score.score
                entry["status"] = "SUCCESS"

                save_results_json(company, icp_score, 
                filename=f"{company.domain}.json",
                output_dir=settings.output_dir
                )

                save_results_csv(
                    company,
                    icp_score,
                    output_dir=settings.output_dir,
                )

                #DB Persistence
                row = company_to_row(company, icp_score) 
                company_id = repository.insert_company(conn,row)
                enrichment_id = repository.insert_enrichment_run(conn,company_id, row)
                repository.insert_qualification_result(
                    conn,
                    company_id,
                    enrichment_id,
                    row["icp_score"],
                    row["is_qualified"],
                    )
                conn.commit()

            except Exception as e:
                entry["status"] = "FAIL"
                entry["error_type"] = type(e).__name__
                entry["error_message"] = str(e)

    batch = order_and_rank_batch(batch) 
    save_batch_summary(batch)
    output_summary(batch)
    
    return 0



def main() -> int:
    settings = Settings.from_env()
    conn = get_connection(settings.database_url)
    try:
        create_tables(conn)

        args = parse_args()
        if args.csv: 
            return process_batch(conn, args.csv, settings)

        if args.domain:
            return process_single_domain(conn, args.domain, settings)
            
        if args.get_specific_industry:
            results = repository.get_industry_count(
                conn, args.get_specific_industry
            )
            for row in results:
                print(row)
            return
        
        
        match args.query:
            case "get-specific-industry":
                select_industry_list = repository.get_industry_count(conn, "Computer software") 
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
                failed_list = repository.get_failed(conn)
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
                

    finally:
        conn.close()

# Entry-point validation
if __name__ == "__main__":
    raise SystemExit(main())

