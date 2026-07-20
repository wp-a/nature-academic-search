from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from nature_academic_search.errors import DataSourceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT / "tests" / "fixtures" / "sources" / "semantic-scholar-search.json"
)


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def config(*, api_key: str = "s2-test") -> SimpleNamespace:
    return SimpleNamespace(
        semantic_scholar_api_key=api_key,
        semantic_scholar_timeout=15,
        max_rows=50,
    )


def test_search_normalizes_semantic_scholar_paper() -> None:
    from nature_academic_search.sources.semantic_scholar import SemanticScholarSource

    with (
        patch(
            "nature_academic_search.sources.semantic_scholar.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.semantic_scholar.request_json",
            return_value=(load_fixture(), {}),
        ) as request,
    ):
        result = SemanticScholarSource().search("example", rows=5)

    assert request.call_args.kwargs["url"].endswith("/paper/search")
    assert request.call_args.kwargs["params"]["query"] == "example"
    assert request.call_args.kwargs["params"]["limit"] == 5
    assert "citationCount" in request.call_args.kwargs["params"]["fields"]
    assert request.call_args.kwargs["headers"] == {"x-api-key": "s2-test"}
    record = result["results"][0]
    assert record["entity_type"] == "publication"
    assert record["semantic_scholar_id"] == (
        "0123456789abcdef0123456789abcdef01234567"
    )
    assert record["source_id"] == record["semantic_scholar_id"]
    assert record["doi"] == "10.1000/example"
    assert record["arxiv_id"] == "2401.12345"
    assert record["pmid"] == "12345678"
    assert record["authors"] == ["Researcher One"]
    assert record["citation_count"] == 6
    assert record["citation_count_source"] == "semantic_scholar"
    assert record["citation_counts"] == {"semantic_scholar": 6}
    assert record["reference_count"] == 4
    assert record["reference_count_source"] == "semantic_scholar"
    assert record["fulltext_url"] == "https://example.test/article.pdf"


def test_search_omits_empty_key_and_caps_rows() -> None:
    from nature_academic_search.sources.semantic_scholar import SemanticScholarSource

    with (
        patch(
            "nature_academic_search.sources.semantic_scholar.get_config",
            return_value=config(api_key=""),
        ),
        patch(
            "nature_academic_search.sources.semantic_scholar.request_json",
            return_value=({"total": 0, "data": []}, {}),
        ) as request,
    ):
        SemanticScholarSource().search("example", rows=500)

    assert request.call_args.kwargs["headers"] == {}
    assert request.call_args.kwargs["params"]["limit"] == 50


def test_adapter_throttles_consecutive_requests() -> None:
    from nature_academic_search.sources.semantic_scholar import SemanticScholarSource

    source = SemanticScholarSource()
    with (
        patch(
            "nature_academic_search.sources.semantic_scholar.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.semantic_scholar.request_json",
            return_value=({"total": 0, "data": []}, {}),
        ),
        patch(
            "nature_academic_search.sources.semantic_scholar.time.monotonic",
            side_effect=[10.0, 10.2],
        ),
        patch("nature_academic_search.sources.semantic_scholar.time.sleep") as sleep,
    ):
        source.search("first")
        source.search("second")

    sleep.assert_called_once_with(pytest.approx(0.8))


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("10.1000/example", "DOI:10.1000/example"),
        ("2401.12345", "ARXIV:2401.12345"),
        ("PMID:12345678", "PMID:12345678"),
        (
            "https://www.semanticscholar.org/paper/"
            "0123456789abcdef0123456789abcdef01234567",
            "0123456789abcdef0123456789abcdef01234567",
        ),
    ],
)
def test_get_by_id_uses_semantic_scholar_identifier_prefixes(
    identifier: str, expected: str
) -> None:
    from nature_academic_search.sources.semantic_scholar import SemanticScholarSource

    paper = load_fixture()["data"][0]
    with (
        patch(
            "nature_academic_search.sources.semantic_scholar.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.semantic_scholar.request_json",
            return_value=(paper, {}),
        ) as request,
    ):
        record = SemanticScholarSource().get_by_id(identifier)

    assert request.call_args.kwargs["url"].endswith(f"/paper/{expected}")
    assert record["semantic_scholar_id"] == paper["paperId"]


def test_search_rejects_empty_query_and_malformed_payload() -> None:
    from nature_academic_search.sources.semantic_scholar import SemanticScholarSource

    with pytest.raises(DataSourceError, match="Empty search query"):
        SemanticScholarSource().search(" ")

    with (
        patch(
            "nature_academic_search.sources.semantic_scholar.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.semantic_scholar.request_json",
            return_value=({"total": 1, "data": {}}, {}),
        ),
        pytest.raises(DataSourceError, match="Malformed search response"),
    ):
        SemanticScholarSource().search("example")
