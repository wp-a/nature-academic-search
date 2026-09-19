from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest


def config() -> SimpleNamespace:
    return SimpleNamespace(
        pubmed_email="researcher@example.com",
        pubmed_api_key="",
        max_rows=50,
    )


def response(*, content: bytes = b"", payload: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        json=lambda: payload,
    )


def test_lookup_mesh_uses_esummary_for_descriptor_metadata() -> None:
    from nature_academic_search.sources.pubmed import PubMedSource

    search_xml = b"""\
<eSearchResult>
  <IdList><Id>68001185</Id><Id>2108164</Id></IdList>
</eSearchResult>
"""
    summary = {
        "result": {
            "uids": ["68001185", "2108164"],
            "68001185": {
                "ds_meshterms": ["Artificial Intelligence", "Computer Reasoning"],
                "ds_meshui": "D001185",
            },
            "2108164": {
                "ds_meshterms": ["Generative Artificial Intelligence", "GenAI"],
                "ds_meshui": "D000098842",
            },
        }
    }

    with (
        patch(
            "nature_academic_search.sources.pubmed.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.pubmed._get",
            side_effect=[
                response(content=search_xml),
                response(payload=summary),
            ],
        ) as request,
    ):
        result = PubMedSource().lookup_mesh("Artificial Intelligence")

    assert result == {
        "term": "Artificial Intelligence",
        "results": [
            {
                "name": "Artificial Intelligence",
                "mesh_id": "D001185",
                "ui": "D001185",
            },
            {
                "name": "Generative Artificial Intelligence",
                "mesh_id": "D000098842",
                "ui": "D000098842",
            },
        ],
    }
    endpoint, params = request.call_args_list[1].args
    assert endpoint == "esummary.fcgi"
    assert params == {
        "db": "mesh",
        "id": "68001185,2108164",
        "retmode": "json",
        "version": "2.0",
    }


def _retry_config() -> SimpleNamespace:
    return SimpleNamespace(
        pubmed_email="researcher@example.com",
        pubmed_api_key="",
        max_rows=50,
    )


def _ok_response() -> SimpleNamespace:
    return SimpleNamespace(raise_for_status=lambda: None, text="<xml/>")


def test_get_retries_connection_errors_and_succeeds() -> None:
    import requests

    from nature_academic_search.sources import pubmed

    with (
        patch.object(pubmed, "get_config", return_value=_retry_config()),
        patch.object(pubmed.time, "sleep") as sleep,
        patch.object(
            pubmed.requests,
            "get",
            side_effect=[
                requests.ConnectionError("reset by peer"),
                requests.ConnectionError("reset by peer"),
                _ok_response(),
            ],
        ) as get,
    ):
        response = pubmed._get("esearch.fcgi", {"db": "pubmed", "term": "cancer"})

    assert response.text == "<xml/>"
    assert get.call_count == 3
    # linear retry backoff: 1s after the first failure, 2s after the second
    # (throttle sleeps are sub-second and filtered out)
    backoff_delays = [c.args[0] for c in sleep.call_args_list if c.args[0] >= 1]
    assert backoff_delays == [1, 2]


def test_get_reports_exception_class_and_attempt_count() -> None:
    import requests

    from nature_academic_search.errors import DataSourceError
    from nature_academic_search.sources import pubmed

    with (
        patch.object(pubmed, "get_config", return_value=_retry_config()),
        patch.object(pubmed.time, "sleep"),
        patch.object(
            pubmed.requests,
            "get",
            side_effect=requests.ConnectionError("reset by peer"),
        ) as get,
    ):
        with pytest.raises(DataSourceError) as excinfo:
            pubmed._get("esearch.fcgi", {"db": "pubmed", "term": "cancer"})

    message = str(excinfo.value)
    assert "ConnectionError" in message
    assert "3 attempts" in message
    assert get.call_count == 3


def test_get_does_not_retry_timeouts() -> None:
    import requests

    from nature_academic_search.errors import DataSourceError
    from nature_academic_search.sources import pubmed

    with (
        patch.object(pubmed, "get_config", return_value=_retry_config()),
        patch.object(pubmed.time, "sleep") as sleep,
        patch.object(
            pubmed.requests,
            "get",
            side_effect=requests.Timeout("timed out"),
        ) as get,
    ):
        with pytest.raises(DataSourceError) as excinfo:
            pubmed._get("esearch.fcgi", {"db": "pubmed", "term": "cancer"})

    assert "timed out" in str(excinfo.value)
    assert get.call_count == 1
    # no retry backoff occurred; only the sub-second throttle sleep may fire
    assert all(c.args[0] < 1 for c in sleep.call_args_list)
