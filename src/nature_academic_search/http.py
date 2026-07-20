"""Secret-safe JSON requests for external academic data sources."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import requests

from .errors import DataSourceError

RETRYABLE_STATUSES = {429, 502, 503, 504}
RESPONSE_METADATA_HEADERS = (
    "x-ratelimit-credits-used",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "retry-after",
)
MAX_RETRY_AFTER_SECONDS = 30.0


def request_json(
    *,
    source: str,
    method: str,
    url: str,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int | float = 30,
    max_retries: int = 2,
) -> tuple[Any, dict[str, str]]:
    """Request JSON with bounded retries and credential-safe errors."""
    session = requests.Session()
    safe_url = url.split("?", 1)[0]

    for attempt in range(max_retries + 1):
        try:
            response = session.request(
                method,
                url,
                params=dict(params or {}),
                headers=dict(headers or {}),
                timeout=timeout,
            )
        except requests.Timeout:
            if attempt < max_retries:
                time.sleep(_backoff_seconds(attempt, {}))
                continue
            raise DataSourceError(source, f"Request timed out: {safe_url}") from None
        except requests.RequestException:
            if attempt < max_retries:
                time.sleep(_backoff_seconds(attempt, {}))
                continue
            raise DataSourceError(source, f"Request failed: {safe_url}") from None

        if response.status_code in RETRYABLE_STATUSES and attempt < max_retries:
            time.sleep(_backoff_seconds(attempt, response.headers))
            continue
        if response.status_code >= 400:
            raise DataSourceError(
                source,
                f"HTTP {response.status_code} from {safe_url}",
            )

        try:
            payload = response.json()
        except ValueError:
            raise DataSourceError(source, f"invalid JSON from {safe_url}") from None
        return payload, _response_metadata(response.headers)

    raise AssertionError("request retry loop exited unexpectedly")


def _backoff_seconds(attempt: int, headers: Mapping[str, str]) -> float:
    retry_after = next(
        (value for key, value in headers.items() if key.casefold() == "retry-after"),
        None,
    )
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), MAX_RETRY_AFTER_SECONDS)
        except ValueError:
            pass
    return min(float(2**attempt), MAX_RETRY_AFTER_SECONDS)


def _response_metadata(headers: Mapping[str, str]) -> dict[str, str]:
    normalized = {key.casefold(): str(value) for key, value in headers.items()}
    return {
        key: normalized[key]
        for key in RESPONSE_METADATA_HEADERS
        if key in normalized
    }
