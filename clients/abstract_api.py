import time
from collections.abc import Callable

import requests


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AbstractAPIError(Exception):
    pass


class AbstractAPIClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise AbstractAPIError("ABSTRACT_API_KEY is not configured.")

        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._session = session or requests.Session()
        self._sleep = sleep

    def _wait_before_retry(self, attempt: int) -> None:
        self._sleep(self._backoff_seconds * (2**attempt))

    def get_company_by_domain(self, domain: str) -> dict:
        params = {
            "api_key": self._api_key,
            "domain": domain,
        }

        for attempt in range(self._max_retries + 1):
            try:
                response = self._session.get(
                    self._base_url,
                    params=params,
                    timeout=self._timeout_seconds,
                )

                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt < self._max_retries:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            self._sleep(float(retry_after))
                        else:
                            self._wait_before_retry(attempt)
                        continue

                if response.status_code == 400:
                    raise AbstractAPIError(f"Invalid request for domain: {domain}")
                if response.status_code == 401:
                    raise AbstractAPIError("Abstract API key is invalid or missing.")
                if response.status_code == 403:
                    raise AbstractAPIError("Abstract API request is forbidden.")
                if response.status_code == 404:
                    raise AbstractAPIError(f"Company not found for domain: {domain}")
                if response.status_code == 429:
                    raise AbstractAPIError(
                        "Abstract API rate limit exceeded after retries."
                    )
                if 500 <= response.status_code < 600:
                    raise AbstractAPIError(
                        "Abstract API server error after retries: "
                        f"{response.status_code}"
                    )

                response.raise_for_status()

                try:
                    return response.json()
                except ValueError as exc:
                    raise AbstractAPIError(
                        "Abstract API returned invalid JSON."
                    ) from exc

            except requests.Timeout as exc:
                if attempt < self._max_retries:
                    self._wait_before_retry(attempt)
                    continue
                raise AbstractAPIError(
                    f"Abstract API timed out after retries for: {domain}"
                ) from exc

            except requests.ConnectionError as exc:
                if attempt < self._max_retries:
                    self._wait_before_retry(attempt)
                    continue
                raise AbstractAPIError(
                    "Could not connect to Abstract API after retries for: "
                    f"{domain}"
                ) from exc

            except requests.RequestException as exc:
                raise AbstractAPIError(
                    f"Abstract API request failed for: {domain}"
                ) from exc

        raise AbstractAPIError(f"Abstract API request failed for: {domain}")
