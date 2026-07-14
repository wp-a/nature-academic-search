from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nature_academic_search.search import deduplicate_records, search_all  # noqa: E402


def test_duplicate_doi_records_merge_sources_and_citation_count() -> None:
    records = [
        {
            "title": "A paper",
            "doi": "10.1000/ABC",
            "source": "crossref",
            "citation_count": 3,
        },
        {
            "title": "A paper",
            "doi": "https://doi.org/10.1000/abc",
            "source": "pubmed",
            "citation_count": 5,
            "pmid": "12345678",
        },
    ]

    merged = deduplicate_records(records)

    assert len(merged) == 1
    assert merged[0]["doi"] == "10.1000/abc"
    assert merged[0]["pmid"] == "12345678"
    assert merged[0]["sources"] == ["crossref", "pubmed"]
    assert merged[0]["citation_count"] == 5


def test_title_and_year_merge_records_without_shared_identifier() -> None:
    records = [
        {"title": "Prime-editing: a practical guide", "year": 2026, "source": "pubmed"},
        {"title": "Prime editing a practical guide", "year": "2026", "source": "arxiv"},
        {"title": "Prime editing a practical guide", "year": 2025, "source": "crossref"},
    ]

    merged = deduplicate_records(records)

    assert len(merged) == 2
    assert merged[0]["sources"] == ["pubmed", "arxiv"]
    assert merged[1]["sources"] == ["crossref"]


def test_arxiv_versions_are_deduplicated_without_losing_order() -> None:
    records = [
        {"title": "First", "arxiv_id": "2401.12345v2", "source": "arxiv"},
        {
            "title": "First revised",
            "arxiv_id": "https://arxiv.org/abs/2401.12345",
            "source": "crossref",
        },
        {"title": "Second", "pmid": "42", "source": "pubmed"},
    ]

    merged = deduplicate_records(records)

    assert [record["title"] for record in merged] == ["First", "Second"]
    assert merged[0]["arxiv_id"] == "2401.12345"


class FakeSource:
    def __init__(self, result: dict | None = None, error: Exception | None = None):
        self.result = result
        self.error = error

    def search(self, query: str, rows: int = 5, **_: object) -> dict:
        if self.error:
            raise self.error
        assert query == "prime editing"
        assert rows == 5
        return self.result or {"total": 0, "results": []}


def test_search_all_preserves_partial_results_and_reports_failure() -> None:
    adapters = {
        "crossref": FakeSource(
            {"total": 1, "results": [{"title": "Shared", "doi": "10.1/x"}]}
        ),
        "pubmed": FakeSource(error=RuntimeError("rate limited")),
        "arxiv": FakeSource(
            {
                "total": 1,
                "results": [
                    {"title": "Shared", "doi": "https://doi.org/10.1/X"},
                ],
            }
        ),
    }

    result = asyncio.run(
        search_all(
            "prime editing",
            ["crossref", "pubmed", "arxiv"],
            rows=5,
            adapters=adapters,
        )
    )

    assert result["total"] == 2
    assert result["raw_result_count"] == 2
    assert result["result_count"] == 1
    assert result["sources_queried"] == ["crossref", "pubmed", "arxiv"]
    assert result["results"][0]["sources"] == ["crossref", "arxiv"]
    assert result["errors"] == [{"source": "pubmed", "error": "rate limited"}]
