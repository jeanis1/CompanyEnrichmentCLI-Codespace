import time

import requests

ABSTRACT_COMPANY_URL = "https://companyenrichment.abstractapi.com/v1/"


MAX_RETRIES = 3
BACKOFF_SECONDS = 1 

# Temporary failures that may succeed if retried
RETRYABLE_STATUS_CODES = { 
    429, # Too many requests
    500, # Internal server error
    502, # Bad Gateway
    503, # Service unavailable
    504, # Gateway Timeout
}
class AbstractAPIError(Exception):
    pass

def _wait_before_retry(attempt: int) -> None: 
    delay = BACKOFF_SECONDS * (2 ** attempt)
    time.sleep(delay)

def get_company_by_domain(
    domain: str,
    *,
    api_key: str,
) -> dict : 
    
    params = { 
        "api_key": api_key,
        "domain": domain,
    }

    for attempt in range(MAX_RETRIES + 1):
        try: 
            response = requests.get(
                ABSTRACT_COMPANY_URL,
                params=params,
                timeout=10
            )

            # -----------------------
            # Retry temporary HTTP failures
            # -----------------------

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < MAX_RETRIES:

                    # If the API tells us how long to wait,
                    # prefer that over our own backoff.
                    retry_after = response.headers.get("Retry-After")

                    if retry_after and retry_after.isdigit(): 
                        time.sleep(int(retry_after))
                    else: 
                        _wait_before_retry(attempt)

                    continue

            # -----------------------
            # Non-retryable API errors
            # -----------------------

            if response.status_code == 400:
                raise AbstractAPIError(
                    f"Invalid request for domain: {domain}"
                )

            if response.status_code == 401: 
                raise AbstractAPIError(
                    "Abstract API key is invalid or missing."
                )

            if response.status_code == 403:
                raise AbstractAPIError(
                    "Abstract API request is forbidden."
                )

            if response.status_code == 404:
                raise AbstractAPIError(
                    f"Company not found for domain: {domain}"
                )
            
        # -----------------------
        # Retries exhausted
        # -----------------------

            if response.status_code == 429:
                raise AbstractAPIError(
                    "Abstract API rate limit exceeded after retries."
                )

            if 500 <= response.status_code < 600:
                raise AbstractAPIError(
                    f"Abstract API server error after retries: "
                    f"{response.status_code}"
                )

            # Catch any other HTTP errors
            response.raise_for_status()

            break


        # -----------------------
        # Network errors
        # -----------------------

        except requests.Timeout as exc: 
            if attempt < MAX_RETRIES: 
                _wait_before_retry(attempt)
                continue

            raise AbstractAPIError(
                f"Abstract API timed out after retries for: {domain}"
            ) from exc

        except requests.ConnectionError as exc:
            if attempt < MAX_RETRIES: 
                _wait_before_retry(attempt)
                continue

            raise AbstractAPIError(
                f"Could not connect to Abstract API "
                f"after retries for: {domain}"
            ) from exc 

        except requests.RequestException as exc:
            raise AbstractAPIError(
                f"Abstract API request failed for: {domain}"
            ) from exc

    # -----------------------
    # Validate response as JSON
    # -----------------------

    try: 
        data = response.json()

    except requests.JSONDecodeError as exc: 
        raise AbstractAPIError(
            "Abstract API returned invalid JSON."
        ) from exc
    return data
