import pandas as pd
import re 

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
            entry["error_type"] = "Duplicate"
            entry["error_message"] = f"Duplicate domain found in input CSV: {domain}"
    
    return batch


def remove_database_duplication(batch: list[dict]) -> list[dict]:
    # reference existing Database
    df = pd.read_csv("data/output/results.csv")
    existing_domains=set(
        df["Domain"]
        .dropna()
        .str.strip()
        .str.lower()
    )
    for entry in batch: 
        domain = entry["domain"].strip().lower()

        if domain in existing_domains: 
            entry["status"] = "FAIL"
            entry["error_type"] = "Previous Existing"
            entry["error_message"] = f"Domain {domain} already exists in the database."
    return batch





def build_list(results:list[dict]) -> None:
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))


    