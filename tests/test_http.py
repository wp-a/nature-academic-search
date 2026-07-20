from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from nature_academic_search.config import Config
from nature_academic_search.errors import DataSourceError


@dataclass
class FakeResponse:
    status_code: int
    payload: object = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    json_error: ValueError | None = None

    def json(self) -> object:
        if self.json_error is not None:
            raise self.json_error
        return self.payload


def test_new_source_configuration_is_environment_driven(monkeypatch) -> None:
    monkeypatch.setenv("OPENALEX_API_KEY", "openalex-test")
    monkeypatch.setenv("OPENALEX_TIMEOUT", "13")
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "s2-test")
    monkeypatch.setenv("SEMANTIC_SCHOLAR_TIMEOUT", "15")
    monkeypatch.setenv("EUROPE_PMC_TIMEOUT", "17")
    monkeypatch.setenv("CLINICALTRIALS_GOV_TIMEOUT", "19")

    config = Config()

    assert config.openalex_api_key == "openalex-test"
    assert config.openalex_timeout == 13
    assert config.semantic_scholar_api_key == "s2-test"
    assert config.semantic_scholar_timeout == 15
    assert config.europe_pmc_timeout == 17
    assert config.clinicaltrials_gov_timeout == 19


def test_new_source_configuration_uses_toml_fallbacks(
    tmp_path: Path, monkeypatch
) -> None:
    for name in (
        "OPENALEX_API_KEY",
        "OPENALEX_TIMEOUT",
        "SEMANTIC_SCHOLAR_API_KEY",
        "SEMANTIC_SCHOLAR_TIMEOUT",
        "EUROPE_PMC_TIMEOUT",
        "CLINICALTRIALS_GOV_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / "sources.toml"
    path.write_text(
        """
[openalex]
api_key = "toml-openalex"
timeout = 21

[semantic_scholar]
api_key = "toml-s2"
timeout = 22

[europe_pmc]
timeout = 23

[clinicaltrials_gov]
timeout = 24
""".strip(),
        encoding="utf-8",
    )

    config = Config(path)

    assert config.openalex_api_key == "toml-openalex"
    assert config.openalex_timeout == 21
    assert config.semantic_scholar_api_key == "toml-s2"
    assert config.semantic_scholar_timeout == 22
    assert config.europe_pmc_timeout == 23
    assert config.clinicaltrials_gov_timeout == 24


def test_invalid_source_timeout_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("OPENALEX_TIMEOUT", "not-a-number")

    with pytest.raises(ValueError):
        _ = Config().openalex_timeout


def test_request_json_returns_payload_and_rate_metadata() -> None:
    from nature_academic_search.http import request_json

    response = FakeResponse(
        200,
        {"results": []},
        {
            "X-RateLimit-Remaining": "42",
            "X-RateLimit-Credits-Used": "10",
            "Unrelated": "ignored",
        },
    )

    with patch("requests.Session.request", return_value=response) as request:
        payload, metadata = request_json(
            source="openalex",
            method="GET",
            url="https://api.openalex.org/works",
            timeout=13,
        )

    assert payload == {"results": []}
    assert metadata == {
        "x-ratelimit-credits-used": "10",
        "x-ratelimit-remaining": "42",
    }
    assert request.call_args.kwargs["timeout"] == 13


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_request_json_retries_retryable_statuses(status: int) -> None:
    from nature_academic_search.http import request_json

    responses = [
        FakeResponse(status, {"error": "temporary"}),
        FakeResponse(status, {"error": "temporary"}),
        FakeResponse(200, {"ok": True}),
    ]

    with (
        patch("requests.Session.request", side_effect=responses) as request,
        patch("nature_academic_search.http.time.sleep") as sleep,
    ):
        payload, _ = request_json(
            source="example",
            method="GET",
            url="https://example.test/api",
        )

    assert payload == {"ok": True}
    assert request.call_count == 3
    assert sleep.call_count == 2


def test_request_json_honors_bounded_numeric_retry_after() -> None:
    from nature_academic_search.http import request_json

    responses = [
        FakeResponse(429, headers={"Retry-After": "120"}),
        FakeResponse(200, {"ok": True}),
    ]

    with (
        patch("requests.Session.request", side_effect=responses),
        patch("nature_academic_search.http.time.sleep") as sleep,
    ):
        request_json(
            source="example",
            method="GET",
            url="https://example.test/api",
        )

    sleep.assert_called_once_with(30.0)


@pytest.mark.parametrize("status", [400, 404])
def test_request_json_does_not_retry_non_retryable_statuses(status: int) -> None:
    from nature_academic_search.http import request_json

    with (
        patch(
            "requests.Session.request",
            return_value=FakeResponse(status, {"error": "bad request"}),
        ) as request,
        pytest.raises(DataSourceError, match=f"HTTP {status}"),
    ):
        request_json(
            source="example",
            method="GET",
            url="https://example.test/api",
        )

    assert request.call_count == 1


def test_request_json_converts_timeout_without_leaking_secrets() -> None:
    from nature_academic_search.http import request_json

    with (
        patch(
            "requests.Session.request",
            side_effect=requests.Timeout("token=super-secret"),
        ),
        pytest.raises(DataSourceError) as error,
    ):
        request_json(
            source="semantic_scholar",
            method="GET",
            url="https://example.test/api",
            params={"api_key": "super-secret"},
            headers={"x-api-key": "super-secret"},
            max_retries=0,
        )

    assert "super-secret" not in str(error.value)
    assert "timed out" in str(error.value).lower()
    formatted = "".join(
        traceback.format_exception(
            type(error.value),
            error.value,
            error.value.__traceback__,
        )
    )
    assert "super-secret" not in formatted


def test_request_json_rejects_malformed_json() -> None:
    from nature_academic_search.http import request_json

    response = FakeResponse(200, json_error=ValueError("invalid payload"))

    with (
        patch("requests.Session.request", return_value=response),
        pytest.raises(DataSourceError, match="invalid JSON"),
    ):
        request_json(
            source="example",
            method="GET",
            url="https://example.test/api",
        )
