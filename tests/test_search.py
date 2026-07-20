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
        self.calls: list[tuple[str, int, dict]] = []

    def search(self, query: str, rows: int = 5, **_: object) -> dict:
        self.calls.append((query, rows, dict(_)))
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
    assert result["sources_succeeded"] == ["crossref", "arxiv"]
    assert result["sources_skipped"] == []
    assert result["results"][0]["sources"] == ["crossref", "arxiv"]
    assert result["errors"][0]["source"] == "pubmed"
    assert result["errors"][0]["error"] == "rate limited"


def test_search_all_uses_five_default_publication_sources() -> None:
    source_names = ["crossref", "pubmed", "arxiv", "openalex", "europe_pmc"]
    adapters = {
        source: FakeSource({"total": 0, "results": [], "source_meta": {}})
        for source in source_names
    }

    result = asyncio.run(
        search_all(
            "prime editing",
            None,
            rows=5,
            adapters=adapters,
        )
    )

    assert result["sources_queried"] == source_names
    assert result["sources_succeeded"] == source_names
    assert result["sources_skipped"] == []
    assert result["errors"] is None
    assert all(adapter.calls for adapter in adapters.values())


def test_pubmed_and_europe_pmc_merge_by_pmid_and_preserve_provenance() -> None:
    records = [
        {
            "entity_type": "publication",
            "title": "Example study",
            "year": 2025,
            "pmid": "12345678",
            "source": "pubmed",
            "source_id": "12345678",
            "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345678",
        },
        {
            "entity_type": "publication",
            "title": "Example study",
            "year": 2025,
            "pmid": "12345678",
            "pmcid": "PMC1234567",
            "source": "europe_pmc",
            "source_id": "MED:12345678",
            "source_url": "https://europepmc.org/article/MED/12345678",
        },
    ]

    merged = deduplicate_records(records)

    assert len(merged) == 1
    assert merged[0]["pmcid"] == "PMC1234567"
    assert merged[0]["sources"] == ["pubmed", "europe_pmc"]
    assert merged[0]["source_records"] == [
        {
            "source": "pubmed",
            "source_id": "12345678",
            "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345678",
        },
        {
            "source": "europe_pmc",
            "source_id": "MED:12345678",
            "source_url": "https://europepmc.org/article/MED/12345678",
        },
    ]


def test_citation_counts_remain_source_attributed_after_merge() -> None:
    records = [
        {
            "title": "Example study",
            "doi": "10.1000/example",
            "source": "openalex",
            "citation_count": 7,
            "citation_count_source": "openalex",
            "citation_counts": {"openalex": 7},
        },
        {
            "title": "Example study",
            "doi": "10.1000/example",
            "source": "crossref",
            "citation_count": 9,
        },
    ]

    merged = deduplicate_records(records)

    assert merged[0]["citation_count"] == 9
    assert merged[0]["citation_count_source"] == "crossref"
    assert merged[0]["citation_counts"] == {"openalex": 7, "crossref": 9}


def test_conflicting_identifiers_are_retained_without_overwrite() -> None:
    records = [
        {
            "title": "Example study",
            "year": 2025,
            "doi": "10.1000/example",
            "pmid": "12345678",
            "source": "openalex",
        },
        {
            "title": "Example study",
            "year": 2025,
            "doi": "10.1000/example",
            "pmid": "87654321",
            "source": "europe_pmc",
        },
    ]

    merged = deduplicate_records(records)

    assert merged[0]["pmid"] == "12345678"
    assert merged[0]["conflicts"] == [
        {
            "field": "pmid",
            "kept": "12345678",
            "incoming": "87654321",
            "source": "europe_pmc",
        }
    ]


def test_publication_and_trial_titles_never_merge() -> None:
    records = [
        {
            "entity_type": "publication",
            "title": "Example intervention",
            "year": 2025,
            "source": "pubmed",
        },
        {
            "entity_type": "trial",
            "title": "Example intervention",
            "year": 2025,
            "nct_id": "NCT01234567",
            "source": "clinicaltrials_gov",
        },
    ]

    merged = deduplicate_records(records)

    assert len(merged) == 2


class FakeEnricher:
    def __init__(self, responses: dict[str, dict | Exception]):
        self.responses = responses
        self.calls: list[str] = []

    def get_by_id(self, identifier: str) -> dict:
        self.calls.append(identifier)
        response = self.responses[identifier]
        if isinstance(response, Exception):
            raise response
        return response


def test_semantic_scholar_enrichment_uses_strong_ids_and_preserves_failures() -> None:
    from nature_academic_search.search import enrich_records

    records = [
        {
            "title": "By DOI",
            "doi": "10.1000/example",
            "source": "crossref",
        },
        {
            "title": "By arXiv",
            "arxiv_id": "2401.12345",
            "source": "arxiv",
        },
        {"title": "No identifier", "source": "crossref"},
    ]
    enricher = FakeEnricher(
        {
            "DOI:10.1000/example": {
                "title": "By DOI",
                "doi": "10.1000/example",
                "source": "semantic_scholar",
                "semantic_scholar_id": "s2-doi",
                "citation_count": 11,
                "citation_count_source": "semantic_scholar",
                "citation_counts": {"semantic_scholar": 11},
            },
            "ARXIV:2401.12345": RuntimeError("rate limited"),
        }
    )

    outcome = asyncio.run(
        enrich_records(
            records,
            ["semantic_scholar"],
            adapters={"semantic_scholar": enricher},
            limit=3,
        )
    )

    assert enricher.calls == ["DOI:10.1000/example", "ARXIV:2401.12345"]
    assert outcome["results"][0]["semantic_scholar_id"] == "s2-doi"
    assert outcome["results"][0]["citation_counts"] == {
        "semantic_scholar": 11
    }
    assert outcome["results"][1]["title"] == "By arXiv"
    assert outcome["errors"][0]["source"] == "semantic_scholar"
    assert outcome["skipped"] == [
        {
            "source": "semantic_scholar",
            "record_index": 2,
            "reason": "missing strong identifier",
        }
    ]


def test_enrichment_is_bounded_to_requested_limit() -> None:
    from nature_academic_search.search import enrich_records

    records = [
        {"title": "One", "doi": "10.1000/one", "source": "crossref"},
        {"title": "Two", "doi": "10.1000/two", "source": "crossref"},
    ]
    enricher = FakeEnricher(
        {
            "DOI:10.1000/one": {
                "title": "One",
                "doi": "10.1000/one",
                "source": "semantic_scholar",
            }
        }
    )

    outcome = asyncio.run(
        enrich_records(
            records,
            ["semantic_scholar"],
            adapters={"semantic_scholar": enricher},
            limit=1,
        )
    )

    assert len(outcome["results"]) == 2
    assert enricher.calls == ["DOI:10.1000/one"]
