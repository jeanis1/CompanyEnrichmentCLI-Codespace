import pandas as pd

from config import Settings
from datetime import datetime
from services.domains import normalize_domain
from database import repository


class BatchProcessingError(Exception):
    pass


def initialize_batch_processing(csv_path: str) -> list[dict]:
    try:
        df = pd.read_csv(csv_path)
        df = df[["domain", "source"]]

        results = []

        for row_number, (_, row) in enumerate(df.iterrows(), start=1):
            result = {
                "row_number": row_number,
                "domain": row["domain"],
                "source": row["source"],
                "status": None,
                "icp_score": None,
                "qualification": None,
                "error_type": None,
                "error_message": None,
            }
            results.append(result)
        return results

    except FileNotFoundError as exc:
        raise BatchProcessingError(f"CSV file not found: {exc}") from exc

    except pd.errors.EmptyDataError as exc:
        raise BatchProcessingError(f"CSV file is empty: {exc}") from exc

    except KeyError as exc:
        raise BatchProcessingError(
            f"CSV file is missing required columns: {exc}"
        ) from exc


def validate_input(batch: list[dict]) -> list[dict]:
    for entry in batch:
        domain = entry["domain"]
        try:
            entry["domain"] = normalize_domain(domain)
        except ValueError:
            entry["status"] = "FAIL"
            entry["error_type"] = "Invalid Domain"
            entry["error_message"] = f"Domain is not a valid string: {domain}"

    for entry in batch:
        source = entry["source"]
        if pd.isna(source) or not isinstance(source, str) or not source.strip():
            entry["status"] = "FAIL"
            entry["error_type"] = "Source Missing"
            entry["error_message"] = f"Source is missing: {entry['domain']}"
    return batch


def remove_input_duplication(batch: list[dict]) -> list[dict]:
    seen_domains = set()

    for entry in batch:
        if entry["status"] == "FAIL":
            continue

        domain = entry["domain"]

        if domain in seen_domains:
            entry["status"] = "FAIL"
            entry["error_type"] = "Input Duplicate"
            entry["error_message"] = f"Duplicate domain found in input CSV: {domain}"
        else:
            seen_domains.add(domain)

    return batch


def skip_recently_enriched(conn, batch: list[dict], days: int = 30) -> list[dict]:
    # Skip domains already enriched successfully in the last threshold days (saves API calls)
    domains = [entry["domain"] for entry in batch if entry["status"] is None]
    if not domains:
        return batch

    recent = repository.get_recently_enriched(conn, domains, days)

    for entry in batch:
        if entry["status"] is None and entry["domain"] in recent:
            entry["status"] = "SKIPPED"
            entry["error_type"] = "recently_enriched"
    return batch


def order_and_rank_batch(batch: list[dict]) -> list[dict]:
    for entry in batch:
        if entry["status"] == "FAIL":
            entry["icp_score"] = 0
    ordered_batch = sorted(
        batch,
        key=lambda entry: (entry["icp_score"] if entry["icp_score"] is not None else 0),
        reverse=True,
    )
    print(ordered_batch)
    return ordered_batch


def save_batch_summary(results: list[dict]) -> None:
    results_df = pd.DataFrame(results)
    # Log Batch
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    settings = Settings.from_env()
    output_path = settings.output_dir / f"batch-results_{timestamp}.csv"
    results_df.to_csv(output_path, index=False)
    # Also overwrite most recent for easy access
    recent_path = settings.output_dir / "batch_results_most_recent.csv"
    results_df.to_csv(recent_path, index=False)


def output_summary(results: list[dict]) -> None:
    total_rows = len(results)
    # Valid input (not API called)
    valid_rows = sum(1 for entry in results if entry["status"] == "SUCCESS") + sum(
        1
        for entry in results
        if entry["status"] == "FAIL" and entry["error_type"] == "CompanyEnrichmentError"
    )

    # How many domain API calls were successful
    success_rows = sum(1 for entry in results if entry["status"] == "SUCCESS")
    fail_rows = sum(1 for entry in results if entry["status"] == "FAIL")
    skipped_rows = sum(1 for entry in results if entry["status"] == "SKIPPED")

    print("\nBatch Processing Summary:")
    print(f"Total input rows: {total_rows}")
    print(f"Valid unique accounts processed: {valid_rows}")
    print(f"Failures: {fail_rows}")
    print(f"Skipped: {skipped_rows}")
    print(f"Successfully enriched: {success_rows}")
