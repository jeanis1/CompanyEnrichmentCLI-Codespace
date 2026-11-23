import time
import requests
import random

APOLLO_COMPANY_URL = "https://api.apollo.io/api/v1/organizations/enrich"

MAX_RETRIES = 3
MAX_RETRY_AFTER_SECONDS = 30
TIMEOUT_SECONDS = (3, 10)  # (connect, read)
BACKOFF_SECONDS = 1

# Temporary failures that may succeed if retried
RETRYABLE_STATUS_CODES = {
    429,  # Too many requests
    500,  # Internal server error
    502,  # Bad Gateway
    503,  # Service unavailable
    504,  # Gateway Timeout
}


class ApolloAPIError(Exception):
    # code is a short-machine-readable reason, safe to store in Database
    def __init__(self, message, *, code="request_failed"):
        super().__init__(message)
        self.code = code


def _wait_before_retry(attempt: int) -> None:
    # Spreads retries out so many clients don't retry in lockstep.
    time.sleep(random.uniform(0, BACKOFF_SECONDS * (2**attempt)))


def request_company_by_domain_apollo(
    domain: str,
    *,
    api_key: str,
) -> dict:
    params = {
        "domain": domain,
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
                "accept": "application/json",
                "x-api-key": api_key,
            }

            response = requests.get(
                APOLLO_COMPANY_URL, params=params, headers=headers, timeout=10
            )

            # -----------------------
            # Retry temporary HTTP failures
            # -----------------------

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < MAX_RETRIES:
                    retry_after = response.headers.get("Retry-After")

                    if retry_after and retry_after.isdigit():
                        if int(retry_after) > MAX_RETRY_AFTER_SECONDS:
                            raise ApolloAPIError(
                                "Apollo API asked to wait too long before retrying.",
                                code="rate_limited",
                            )
                        time.sleep(int(retry_after))
                    else:
                        _wait_before_retry(attempt)

                    continue

            # -----------------------
            # Non-retryable API errors
            # -----------------------

            if response.status_code == 400:
                raise ApolloAPIError(
                    f"Invalid request for domain: {domain}",
                    code="bad_request",
                )

            if response.status_code == 401:
                raise ApolloAPIError(
                    "Apollo API key is invalid or missing.",
                    code="auth",
                )

            if response.status_code == 403:
                raise ApolloAPIError(
                    "Apollo API request is forbidden.",
                    code="auth",
                )

            if response.status_code == 404:
                raise ApolloAPIError(
                    f"Company not found for domain: {domain}",
                    code="not_found",
                )

            # -----------------------
            # Retries exhausted
            # -----------------------

            if response.status_code == 429:
                raise ApolloAPIError(
                    "ApolloAPIError API rate limit exceeded after retries.",
                    code="rate_limited",
                )

            if 500 <= response.status_code < 600:
                raise ApolloAPIError(
                    f"Apollo API server error after retries: "
                    f"{response.status_code}",
                    code="server_error",
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

            raise ApolloAPIError(
                f"Apollo API timed out after retries for: {domain}",
                code="timeout",
            ) from exc

        except requests.ConnectionError as exc:
            if attempt < MAX_RETRIES:
                _wait_before_retry(attempt)
                continue

            raise ApolloAPIError(
                f"Could not connect to Apollo API " f"after retries for: {domain}",
                code="connection",
            ) from exc

        except requests.RequestException as exc:
            raise ApolloAPIError(
                f"Apollo API request failed for: {domain}", code="request_failed"
            ) from exc

    # -----------------------
    # Validate response as JSON
    # -----------------------

    try:
        data = response.json()

    except requests.JSONDecodeError as exc:
        raise ApolloAPIError(
            "Apollo API returned invalid JSON.", code="invalid_json"
        ) from exc
    return data
