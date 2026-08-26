from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_server():
    sys.path.insert(0, str(ROOT / "src"))
    try:
        return importlib.import_module("nature_academic_search.server")
    finally:
        sys.path.pop(0)


def test_mcp_exposes_exactly_four_backward_compatible_tools() -> None:
    server = load_server()

    tools = asyncio.run(server.mcp.list_tools())

    assert {tool.name for tool in tools} == {
        "search_papers",
        "get_paper_by_id",
        "get_citation",
        "lookup_mesh",
    }

    search_tool = next(tool for tool in tools if tool.name == "search_papers")
    assert {
        "query",
        "sources",
        "rows",
        "type",
        "entity_type",
        "enrich",
        "filters",
        "ranking",
    } <= set(
        search_tool.inputSchema["properties"]
    )
    paper_tool = next(tool for tool in tools if tool.name == "get_paper_by_id")
    assert {
        "include_relations",
        "relation",
        "depth",
        "rows",
        "relation_sources",
    } <= set(paper_tool.inputSchema["properties"])


def test_empty_identifier_is_rejected_before_source_call() -> None:
    server = load_server()

    with patch.object(server._crossref, "get_by_doi") as get_by_doi:
        result = json.loads(server.get_paper_by_id(""))

    assert result == {"error": "Empty identifier"}
    get_by_doi.assert_not_called()


def test_get_paper_by_id_can_attach_field_level_verification() -> None:
    server = load_server()
    actual = {
        "entity_type": "publication",
        "title": "Resolved",
        "year": 2024,
        "doi": "10.1000/example",
    }

    with patch.object(server._crossref, "get_by_doi", return_value=actual):
        result = json.loads(
            server.get_paper_by_id(
                "10.1000/example",
                expected={
                    "title": "Resolved",
                    "year": "2024",
                    "doi": "https://doi.org/10.1000/EXAMPLE",
                },
            )
        )

    assert result["title"] == "Resolved"
    assert result["verification"]["status"] == "verified"
    assert result["verification"]["fields"]["doi"]["status"] == "match"


def test_get_paper_by_id_rejects_malformed_expected_metadata() -> None:
    server = load_server()

    result = json.loads(server.get_paper_by_id("10.1000/example", expected=["bad"]))

    assert result == {"error": "Expected metadata must be an object"}


def test_get_paper_by_id_can_attach_bounded_citation_graph() -> None:
    server = load_server()
    actual = {
        "entity_type": "publication",
        "record_id": "publication:doi:10.1000/example",
        "doi": "10.1000/example",
        "title": "Resolved",
        "year": 2024,
    }
    graph = {"schema_version": "1", "nodes": [actual], "edges": []}
    with (
        patch.object(server._crossref, "get_by_doi", return_value=actual),
        patch.object(server, "build_citation_graph", return_value=graph) as build,
    ):
        result = json.loads(
            server.get_paper_by_id(
                "10.1000/example",
                include_relations=True,
                relation="references",
                depth=2,
                rows=7,
                relation_sources=["crossref"],
            )
        )

    assert result["citation_graph"] == graph
    build.assert_called_once()
    assert build.call_args.kwargs["depth"] == 2
    assert build.call_args.kwargs["relation_sources"] == ["crossref"]


def test_trial_verification_does_not_compare_paper_only_fields() -> None:
    server = load_server()
    actual = {
        "entity_type": "trial",
        "nct_id": "NCT01234567",
        "title": "A Trial",
        "overall_status": "RECRUITING",
    }

    with patch.object(server._clinicaltrials, "get_by_id", return_value=actual):
        result = json.loads(
            server.get_paper_by_id(
                "NCT01234567",
                expected={"title": "A Trial", "status": "RECRUITING"},
            )
        )

    assert result["verification"]["status"] == "verified"
    assert "journal" not in result["verification"]["fields"]


def test_invalid_search_source_is_rejected_before_search() -> None:
    server = load_server()

    with patch.object(server, "search_all") as search_all:
        result = json.loads(server.search_papers("prime editing", sources=["unknown"]))

    assert result["error"].startswith("Invalid sources")
    search_all.assert_not_called()


def test_identifier_detection_accepts_urls_and_versions() -> None:
    server = load_server()

    assert server.detect_id_type("https://doi.org/10.1000/example") == "doi"
    assert server.detect_id_type("PMID:12345678") == "pmid"
    assert server.detect_id_type("https://arxiv.org/abs/2401.12345v2") == "arxiv"


@pytest.mark.parametrize(
    ("identifier", "expected_type"),
    [
        ("PMC1234567", "pmcid"),
        ("https://europepmc.org/articles/PMC1234567", "pmcid"),
        ("W2741809807", "openalex"),
        ("https://openalex.org/W2741809807", "openalex"),
        ("NCT01234567", "nct"),
        ("https://clinicaltrials.gov/study/NCT01234567", "nct"),
        (
            "https://www.semanticscholar.org/paper/example/abc123",
            "semantic_scholar",
        ),
    ],
)
def test_identifier_detection_accepts_expanded_source_ids(
    identifier: str, expected_type: str
) -> None:
    server = load_server()

    assert server.detect_id_type(identifier) == expected_type


def test_raw_semantic_scholar_id_requires_explicit_type() -> None:
    server = load_server()
    paper_id = "649def34f8be52c8b66281af98ae884c09aef38b"

    with pytest.raises(ValueError, match="Cannot detect"):
        server.detect_id_type(paper_id)

    assert server._resolve_id_type(paper_id, "semantic_scholar") == (
        "semantic_scholar"
    )


def test_explicit_legacy_sources_are_forwarded_without_expansion() -> None:
    server = load_server()
    expected = {
        "total": 0,
        "sources_queried": ["crossref", "pubmed", "arxiv"],
        "raw_result_count": 0,
        "result_count": 0,
        "results": [],
        "errors": None,
    }
    legacy_sources = ["crossref", "pubmed", "arxiv"]

    with patch.object(
        server,
        "search_all",
        new=AsyncMock(return_value=expected),
    ) as search_all:
        result = json.loads(server.search_papers("prime editing", sources=legacy_sources))

    assert result == expected
    assert search_all.await_args.args[:3] == ("prime editing", legacy_sources, 5)


def test_default_search_defers_source_selection_to_publication_search() -> None:
    server = load_server()
    expected = {"entity_type": "publication", "results": [], "errors": None}

    with patch.object(
        server,
        "search_all",
        new=AsyncMock(return_value=expected),
    ) as search_all:
        result = json.loads(server.search_papers("prime editing"))

    assert result == expected
    assert search_all.await_args.args[:3] == ("prime editing", None, 5)
    assert search_all.await_args.kwargs["entity_type"] == "publication"
    assert search_all.await_args.kwargs["enrichers"] == []


def test_trial_search_and_semantic_scholar_enrichment_are_forwarded() -> None:
    server = load_server()
    expected = {"entity_type": "trial", "results": [], "errors": None}

    with patch.object(
        server,
        "search_all",
        new=AsyncMock(return_value=expected),
    ) as search_all:
        result = json.loads(
            server.search_papers(
                "prime editing",
                entity_type="trial",
            )
        )

    assert result == expected
    assert search_all.await_args.args[:3] == ("prime editing", None, 5)
    assert search_all.await_args.kwargs["entity_type"] == "trial"

    publication_expected = {
        "entity_type": "publication",
        "results": [],
        "errors": None,
    }
    with patch.object(
        server,
        "search_all",
        new=AsyncMock(return_value=publication_expected),
    ) as search_all:
        json.loads(
            server.search_papers(
                "prime editing",
                sources=["openalex"],
                enrich=["semantic_scholar"],
            )
        )

    assert search_all.await_args.kwargs["enrichers"] == ["semantic_scholar"]

    with patch.object(
        server,
        "search_all",
        new=AsyncMock(return_value=publication_expected),
    ) as search_all:
        json.loads(
            server.search_papers(
                "prime editing",
                sources=["semantic_scholar"],
            )
        )

    assert search_all.await_args.args[1] == ["semantic_scholar"]


def test_discovery_filters_and_ranking_are_forwarded() -> None:
    server = load_server()
    expected = {"entity_type": "publication", "results": [], "errors": None}
    filters = {"date_from": "2024-01-01", "language": "en"}

    with patch.object(server, "search_all", new=AsyncMock(return_value=expected)) as search_all:
        result = json.loads(
            server.search_papers(
                "AI",
                filters=filters,
                ranking="none",
            )
        )

    assert result == expected
    assert search_all.await_args.kwargs["filters"] == filters
    assert search_all.await_args.kwargs["ranking"] == "none"


def test_discovery_filter_shape_is_rejected_before_search() -> None:
    server = load_server()

    with patch.object(server, "search_all") as search_all:
        result = json.loads(server.search_papers("AI", filters=["bad"]))

    assert result == {"error": "filters must be an object"}
    search_all.assert_not_called()


def test_invalid_entity_source_combination_is_rejected_before_search() -> None:
    server = load_server()

    with patch.object(server, "search_all") as search_all:
        result = json.loads(
            server.search_papers(
                "prime editing",
                sources=["pubmed"],
                entity_type="trial",
            )
        )

    assert result["error"].startswith("Invalid sources")
    search_all.assert_not_called()


@pytest.mark.parametrize(
    ("identifier", "id_type", "source_attribute", "method"),
    [
        ("10.1000/example", "auto", "_crossref", "get_by_doi"),
        ("12345678", "auto", "_pubmed", "get_by_pmid"),
        ("2401.12345", "auto", "_arxiv", "get_by_id"),
        ("PMC1234567", "auto", "_europe_pmc", "get_by_pmcid"),
        ("W2741809807", "auto", "_openalex", "get_by_id"),
        (
            "https://www.semanticscholar.org/paper/example/abc123",
            "auto",
            "_semantic_scholar",
            "get_by_id",
        ),
        ("NCT01234567", "auto", "_clinicaltrials", "get_by_id"),
    ],
)
def test_get_paper_by_id_routes_expanded_identifiers(
    identifier: str,
    id_type: str,
    source_attribute: str,
    method: str,
) -> None:
    server = load_server()
    source = getattr(server, source_attribute)
    expected = {"title": "Resolved", "source": source_attribute.removeprefix("_")}

    with patch.object(source, method, return_value=expected) as lookup:
        result = json.loads(server.get_paper_by_id(identifier, id_type=id_type))

    assert result == expected
    lookup.assert_called_once_with(identifier)


@pytest.mark.parametrize(
    ("identifier", "source_attribute", "method", "normalized"),
    [
        (
            "https://doi.org/10.1000/example",
            "_crossref",
            "get_by_doi",
            "10.1000/example",
        ),
        ("PMID:12345678", "_pubmed", "get_by_pmid", "12345678"),
    ],
)
def test_get_paper_by_id_normalizes_legacy_identifier_wrappers_before_lookup(
    identifier: str,
    source_attribute: str,
    method: str,
    normalized: str,
) -> None:
    server = load_server()
    source = getattr(server, source_attribute)
    expected = {"title": "Resolved"}

    with patch.object(source, method, return_value=expected) as lookup:
        result = json.loads(server.get_paper_by_id(identifier))

    assert result == expected
    lookup.assert_called_once_with(normalized)


def test_get_citation_normalizes_doi_url_before_crossref_request() -> None:
    server = load_server()

    with patch.object(
        server._crossref,
        "get_citation",
        return_value="Formatted citation",
    ) as get_citation:
        result = json.loads(
            server.get_citation("https://doi.org/10.1000/example", style="nature")
        )

    assert result["citation"] == "Formatted citation"
    get_citation.assert_called_once_with("10.1000/example", style="nature")


def test_get_citation_prefers_crossref_when_resolved_record_has_doi() -> None:
    server = load_server()
    paper = {"title": "Resolved", "doi": "10.1000/example"}

    with (
        patch.object(server._europe_pmc, "get_by_pmcid", return_value=paper),
        patch.object(
            server._crossref,
            "get_citation",
            return_value="Formatted citation",
        ) as get_citation,
    ):
        result = json.loads(server.get_citation("PMC1234567", style="nature"))

    assert result["citation"] == "Formatted citation"
    get_citation.assert_called_once_with("10.1000/example", style="nature")


def test_get_citation_labels_basic_fallback_metadata_source() -> None:
    server = load_server()
    paper = {
        "title": "Resolved",
        "authors": ["A. Author"],
        "year": 2026,
        "source": "openalex",
    }

    with patch.object(server._openalex, "get_by_id", return_value=paper):
        result = json.loads(server.get_citation("W2741809807"))

    assert result["metadata_source"] == "openalex"
    assert "Resolved" in result["citation"]


def test_trial_registration_is_rejected_as_paper_citation() -> None:
    server = load_server()

    with patch.object(server._clinicaltrials, "get_by_id") as lookup:
        result = json.loads(server.get_citation("NCT01234567"))

    assert result == {
        "error": "Trial registrations are not paper citations",
        "source": "clinicaltrials_gov",
    }
    lookup.assert_not_called()
