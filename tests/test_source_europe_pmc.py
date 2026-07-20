from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from nature_academic_search.errors import DataSourceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sources" / "europe-pmc-search.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def config() -> SimpleNamespace:
    return SimpleNamespace(europe_pmc_timeout=17, max_rows=50)


def test_search_normalizes_europe_pmc_publication() -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    with (
        patch(
            "nature_academic_search.sources.europe_pmc.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=(load_fixture(), {}),
        ) as request,
    ):
        result = EuropePmcSource().search("example", rows=5)

    assert request.call_args.kwargs["params"] == {
        "query": "example",
        "pageSize": 5,
        "format": "json",
        "resultType": "core",
    }
    assert request.call_args.kwargs["timeout"] == 17
    assert result["total"] == 1
    assert result["source"] == "europe_pmc"
    record = result["results"][0]
    assert record["entity_type"] == "publication"
    assert record["source"] == "europe_pmc"
    assert record["source_id"] == "MED:12345678"
    assert record["title"] == "Example study"
    assert record["authors"] == ["Researcher One"]
    assert record["journal"] == "Example Journal"
    assert record["year"] == 2025
    assert record["publication_date"] == "2025-02-03"
    assert record["doi"] == "10.1000/example"
    assert record["pmid"] == "12345678"
    assert record["pmcid"] == "PMC1234567"
    assert record["publication_type"] == "research article"
    assert record["is_preprint"] is False
    assert "peer_reviewed" not in record
    assert record["is_open_access"] is True
    assert record["fulltext_url"] == "https://europepmc.org/articles/PMC1234567"
    assert record["source_url"] == "https://europepmc.org/article/MED/12345678"
    assert record["retrieved_at"].endswith("Z")


def test_search_caps_rows_and_handles_zero_results() -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    empty = {"hitCount": 0, "resultList": {"result": []}}
    with (
        patch(
            "nature_academic_search.sources.europe_pmc.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=(empty, {}),
        ) as request,
    ):
        result = EuropePmcSource().search("example", rows=500)

    assert result["results"] == []
    assert request.call_args.kwargs["params"]["pageSize"] == 50


@pytest.mark.parametrize(
    ("identifier", "expected_query"),
    [
        ("12345678", "EXT_ID:12345678 AND SRC:MED"),
        ("PMID:12345678", "EXT_ID:12345678 AND SRC:MED"),
        ("PMC1234567", "PMCID:PMC1234567"),
    ],
)
def test_get_by_id_supports_pmid_and_pmcid(
    identifier: str, expected_query: str
) -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    with (
        patch(
            "nature_academic_search.sources.europe_pmc.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=(load_fixture(), {}),
        ) as request,
    ):
        record = EuropePmcSource().get_by_id(identifier)

    assert request.call_args.kwargs["params"]["query"] == expected_query
    assert record["pmcid"] == "PMC1234567"


def test_preprint_is_not_reported_as_peer_reviewed() -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    payload = load_fixture()
    payload["resultList"]["result"][0].update(
        {"id": "PPR123", "source": "PPR", "pubType": "preprint"}
    )
    with (
        patch(
            "nature_academic_search.sources.europe_pmc.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=(payload, {}),
        ),
    ):
        record = EuropePmcSource().search("example")["results"][0]

    assert record["is_preprint"] is True
    assert "peer_reviewed" not in record


def test_search_rejects_empty_query_and_malformed_payload() -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    with pytest.raises(DataSourceError, match="Empty search query"):
        EuropePmcSource().search(" ")

    with (
        patch(
            "nature_academic_search.sources.europe_pmc.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=({"hitCount": 1, "resultList": {"result": {}}}, {}),
        ),
        pytest.raises(DataSourceError, match="Malformed search response"),
    ):
        EuropePmcSource().search("example")
