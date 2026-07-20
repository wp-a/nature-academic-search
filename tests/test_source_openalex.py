from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from nature_academic_search.errors import DataSourceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sources" / "openalex-search.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def config(*, api_key: str = "openalex-test") -> SimpleNamespace:
    return SimpleNamespace(
        openalex_api_key=api_key,
        openalex_timeout=13,
        max_rows=50,
    )


def test_search_normalizes_openalex_work_and_usage_metadata() -> None:
    from nature_academic_search.sources.openalex import OpenAlexSource

    rate_meta = {
        "x-ratelimit-remaining": "42",
        "x-ratelimit-credits-used": "10",
    }
    with (
        patch(
            "nature_academic_search.sources.openalex.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.openalex.request_json",
            return_value=(load_fixture(), rate_meta),
        ) as request,
    ):
        result = OpenAlexSource().search("example", rows=5)

    params = request.call_args.kwargs["params"]
    assert params["search"] == "example"
    assert params["per_page"] == 5
    assert params["api_key"] == "openalex-test"
    assert "abstract_inverted_index" in params["select"]
    assert request.call_args.kwargs["timeout"] == 13

    assert result["total"] == 1
    assert result["source"] == "openalex"
    assert result["source_meta"] == {
        "cost_usd": 0.001,
        "rate_limit": rate_meta,
    }
    record = result["results"][0]
    assert record["entity_type"] == "publication"
    assert record["source"] == "openalex"
    assert record["source_id"] == "W1234567890"
    assert record["openalex_id"] == "W1234567890"
    assert record["doi"] == "10.1000/example"
    assert record["pmid"] == "12345678"
    assert record["pmcid"] == "PMC1234567"
    assert record["title"] == "Example study"
    assert record["authors"] == ["Researcher One"]
    assert record["year"] == 2025
    assert record["journal"] == "Example Journal"
    assert record["abstract"] == "A fictional abstract."
    assert record["citation_count"] == 7
    assert record["citation_count_source"] == "openalex"
    assert record["citation_counts"] == {"openalex": 7}
    assert record["is_open_access"] is True
    assert record["fulltext_url"] == "https://example.test/article.pdf"
    assert record["source_records"] == [
        {
            "source": "openalex",
            "source_id": "W1234567890",
            "source_url": "https://openalex.org/W1234567890",
        }
    ]
    assert record["retrieved_at"].endswith("Z")


def test_search_omits_empty_api_key_and_caps_rows() -> None:
    from nature_academic_search.sources.openalex import OpenAlexSource

    empty = {"meta": {"count": 0}, "results": []}
    with (
        patch(
            "nature_academic_search.sources.openalex.get_config",
            return_value=config(api_key=""),
        ),
        patch(
            "nature_academic_search.sources.openalex.request_json",
            return_value=(empty, {}),
        ) as request,
    ):
        result = OpenAlexSource().search("example", rows=500)

    assert result["results"] == []
    assert request.call_args.kwargs["params"]["per_page"] == 50
    assert "api_key" not in request.call_args.kwargs["params"]


@pytest.mark.parametrize(
    ("identifier", "expected_suffix"),
    [
        ("W1234567890", "/W1234567890"),
        ("https://openalex.org/W1234567890", "/W1234567890"),
        ("10.1000/example", "/https://doi.org/10.1000/example"),
    ],
)
def test_get_by_id_supports_openalex_urls_and_doi(
    identifier: str, expected_suffix: str
) -> None:
    from nature_academic_search.sources.openalex import OpenAlexSource

    work = load_fixture()["results"][0]
    with (
        patch(
            "nature_academic_search.sources.openalex.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.openalex.request_json",
            return_value=(work, {}),
        ) as request,
    ):
        record = OpenAlexSource().get_by_id(identifier)

    assert request.call_args.kwargs["url"].endswith(expected_suffix)
    assert record["openalex_id"] == "W1234567890"


def test_search_rejects_empty_query_and_malformed_payload() -> None:
    from nature_academic_search.sources.openalex import OpenAlexSource

    with pytest.raises(DataSourceError, match="Empty search query"):
        OpenAlexSource().search("  ")

    with (
        patch(
            "nature_academic_search.sources.openalex.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.openalex.request_json",
            return_value=({"meta": {}, "results": {}}, {}),
        ),
        pytest.raises(DataSourceError, match="Malformed search response"),
    ):
        OpenAlexSource().search("example")
