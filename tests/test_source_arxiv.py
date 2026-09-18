from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from nature_academic_search.errors import DataSourceError
from nature_academic_search.sources.arxiv import ArxivSource


def _config() -> SimpleNamespace:
    return SimpleNamespace(arxiv_timeout=30)


def _ok_response(text: str = "<feed/>") -> SimpleNamespace:
    return SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        text=text,
    )


def test_request_sends_accept_header_via_requests() -> None:
    from nature_academic_search.sources import arxiv

    source = ArxivSource()

    with (
        patch.object(arxiv, "get_config", return_value=_config()),
        patch.object(arxiv.time, "sleep"),
        patch.object(arxiv.requests, "get", return_value=_ok_response()) as get,
    ):
        body = source._request({"search_query": "(attention)", "max_results": 2})

    assert body == "<feed/>"
    url = get.call_args.args[0]
    headers = get.call_args.kwargs["headers"]
    assert url == arxiv.ARXIV_API_URL
    assert get.call_args.kwargs["params"] == {"search_query": "(attention)", "max_results": 2}
    assert headers["User-Agent"] == "academic-search/1.0"
    assert headers["Accept"] == "application/atom+xml, text/xml, */*"
    assert get.call_args.kwargs["timeout"] == 30


def test_request_maps_rate_limiting_to_datasource_error() -> None:
    import requests

    from nature_academic_search.sources import arxiv

    source = ArxivSource()
    response = SimpleNamespace(status_code=429, raise_for_status=None)
    http_error = requests.HTTPError("429", response=response)

    def raise_for_status() -> None:
        raise http_error

    response.raise_for_status = raise_for_status

    with (
        patch.object(arxiv, "get_config", return_value=_config()),
        patch.object(arxiv.time, "sleep"),
        patch.object(arxiv.requests, "get", return_value=response),
    ):
        with pytest.raises(DataSourceError) as excinfo:
            source._request({"search_query": "(attention)"})

    assert "Rate limited" in str(excinfo.value)
    assert "429" in str(excinfo.value)


def test_request_maps_timeout_to_datasource_error() -> None:
    import requests

    from nature_academic_search.sources import arxiv

    source = ArxivSource()

    with (
        patch.object(arxiv, "get_config", return_value=_config()),
        patch.object(arxiv.time, "sleep"),
        patch.object(arxiv.requests, "get", side_effect=requests.Timeout("slow")),
    ):
        with pytest.raises(DataSourceError) as excinfo:
            source._request({"search_query": "(attention)"})

    assert "timed out" in str(excinfo.value)
