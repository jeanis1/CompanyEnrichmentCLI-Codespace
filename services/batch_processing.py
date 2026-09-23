import pandas as pd
import re 

from config import Settings
from datetime import datetime

DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)


class BatchProcessingError(Exception):
    pass



def initialize_batch_processing(csv_path: str) -> list[dict]:
    try:
        df = pd.read_csv(csv_path)
        df = df[["domain", "source"]]

        results = []

        for row_number, (_, row) in enumerate(df.iterrows(), start=1): 
            domain  = row["domain"]
            source = row["source"]
            
            result = {
                    "row_number": row_number,
                    "domain": domain,
                    "source": source,
                    "status": None,
                    "icp_score": None,
                    "qualification": None,
                    "error_type": None,
                    "error_message": None,
                }
            results.append(result)
        return results
    
    except FileNotFoundError as exc:
        raise BatchProcessingError(
            f"CSV file not found: {exc}"
            ) from exc

    except pd.errors.EmptyDataError as exc:
        raise BatchProcessingError(
            f"CSV file is empty: {exc}"
        ) from exc
    
    except KeyError as exc:
        raise BatchProcessingError(
            f"CSV file is missing required columns: {exc}"
        ) from exc


def validate_domain_input(batch: list[dict]) -> list[dict]:
    for entry in batch :
        domain = entry["domain"]
        if ( not isinstance(domain, str) 
            or not domain.strip()
            or not DOMAIN_PATTERN.fullmatch(domain.strip())
        ) : 
            entry["status"] = "FAIL"
            entry["error_type"] = "Invalid Domain"
            entry["error_message"] = f"Domain is not a valid string: {domain}"
    return batch    


def remove_input_duplication(batch: list[dict]) -> list[dict]:
    seen_domains = set()

    for entry in batch:
        domain = entry["domain"]
        if domain not in seen_domains:
            seen_domains.add(domain)
        else:
            entry["status"] = "FAIL"
            entry["error_type"] = "Input Duplicate"
            entry["error_message"] = f"Duplicate domain found in input CSV: {domain}"
    
    return batch


def remove_database_duplication(batch: list[dict]) -> list[dict]:
    df = pd.read_csv("data/output/results.csv") 
    existing_database = set(df["domain"].str.strip().str.lower()) 

    for entry in batch: 
        domain = entry["domain"].strip().lower()
        if domain in existing_database:
            entry["status"] = "FAIL"
            entry["error_type"] = "Database Duplicate"
            entry["error_message"] = f"Domain {domain} already exists in the database."
    return batch



def build_list(results:list[dict]) -> None:
    results_df = pd.DataFrame(results)
    # TODO - NEED TO set output path as directory for below two functions:

    # Log Batch
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    settings = Settings.from_env()
    output_path = settings.output_dir / f"batch-results_{timestamp}.csv"
    results_df.to_csv(output_path, index=False)
    # Also save to overwrite most recent for easy access
    recent_path = settings.output_dir / "batch_results_most_recent.csv"
    results_df.to_csv(recent_path, index=False)



def output_summary(results:list[dict]) -> None:
    total_rows = len(results)
    valid_rows = sum(1 for entry in results if entry["status"] is None)
    success_rows = sum(1 for entry in results if entry["status"] == "SUCCESS")
    fail_rows = sum(1 for entry in results if entry["status"] == "FAIL")

    print("\nBatch Processing Summary:")
    print(f"Total input rows: {total_rows}")
    print(f"Valid unique accounts processed: {valid_rows}")
    print(f"Successfully enriched: {success_rows}")
    print(f"Failed: {fail_rows}")
    