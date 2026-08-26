from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


def test_openalex_relations_fetch_references_and_cited_by() -> None:
    from nature_academic_search.sources.openalex import OpenAlexSource

    config = SimpleNamespace(openalex_api_key="", openalex_timeout=10, max_rows=50)
    seed = {
        "id": "https://openalex.org/W1",
        "display_name": "Seed",
        "publication_year": 2024,
        "referenced_works": ["https://openalex.org/W2"],
    }
    cited = {
        "id": "https://openalex.org/W3",
        "display_name": "Citing",
        "publication_year": 2025,
    }
    with (
        patch("nature_academic_search.sources.openalex.get_config", return_value=config),
        patch(
            "nature_academic_search.sources.openalex.request_json",
            side_effect=[
                (seed, {}),
                (
                    {
                        "meta": {"count": 1},
                        "results": [{**seed, "id": "https://openalex.org/W2"}],
                    },
                    {},
                ),
                ({"meta": {"count": 1}, "results": [cited]}, {}),
            ],
        ) as request,
    ):
        result = OpenAlexSource().get_citation_relations(
            "10.1000/seed", "both", rows=3
        )

    assert result["references"][0]["openalex_id"] == "W2"
    assert result["cited_by"][0]["openalex_id"] == "W3"
    assert request.call_count == 3
    assert request.call_args_list[-1].kwargs["params"]["filter"] == "cites:W1"


def test_crossref_relations_normalize_reference_dois_without_incoming_claim() -> None:
    from nature_academic_search.sources.crossref import CrossRefSource

    source = CrossRefSource()
    with patch.object(
        source,
        "_request",
        return_value={
            "reference": [
                {
                    "DOI": "10.1000/ref",
                    "article-title": "Referenced",
                    "year": 2020,
                    "journal-title": "Journal",
                }
            ]
        },
    ):
        result = source.get_citation_relations("10.1000/seed", "both", rows=5)

    assert result["references"][0]["doi"] == "10.1000/ref"
    assert result["references"][0]["title"] == "Referenced"
    assert result["cited_by"] == []


def test_pubmed_relations_use_elink_refs_and_citedin() -> None:
    from nature_academic_search.sources.pubmed import PubMedSource

    response = SimpleNamespace(
        json=lambda: {
            "linksets": [
                {
                    "linksetdbs": [
                        {
                            "linkname": "pubmed_pubmed_refs",
                            "links": ["11111111"],
                        },
                        {
                            "linkname": "pubmed_pubmed_citedin",
                            "links": ["22222222"],
                        },
                    ]
                }
            ]
        }
    )
    source = PubMedSource()
    with (
        patch(
            "nature_academic_search.sources.pubmed.get_config",
            return_value=SimpleNamespace(pubmed_email="x", pubmed_api_key=""),
        ),
        patch("nature_academic_search.sources.pubmed._get", return_value=response),
        patch.object(
            source,
            "get_by_pmid",
            side_effect=lambda pmid: {"pmid": pmid, "title": pmid},
        ),
    ):
        result = source.get_citation_relations("12345678", "both", rows=5)

    assert result["references"] == [{"pmid": "11111111", "title": "11111111"}]
    assert result["cited_by"] == [{"pmid": "22222222", "title": "22222222"}]


def test_europe_pmc_relations_parse_reference_list() -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    config = SimpleNamespace(europe_pmc_timeout=10, max_rows=50)
    payload = {
        "hitCount": 1,
        "referenceList": {
            "reference": [
                {
                    "id": "99999999",
                    "source": "MED",
                    "doi": "10.1000/ref",
                    "title": "Referenced",
                    "pubYear": 2020,
                }
            ]
        },
    }
    with (
        patch("nature_academic_search.sources.europe_pmc.get_config", return_value=config),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=(payload, {}),
        ) as request,
    ):
        result = EuropePmcSource().get_citation_relations("12345678", "references", 5)

    assert result["references"][0]["doi"] == "10.1000/ref"
    assert request.call_args.kwargs["url"].endswith("/MED/12345678/references")


def test_semantic_scholar_relations_request_citations_and_references() -> None:
    from nature_academic_search.sources.semantic_scholar import SemanticScholarSource

    payload = {
        "paperId": "seed",
        "title": "Seed",
        "citations": [{"paperId": "citing", "title": "Citing", "year": 2025}],
        "references": [{"paperId": "cited", "title": "Cited", "year": 2020}],
    }
    source = SemanticScholarSource()
    with patch.object(source, "_request", return_value=(payload, {})) as request:
        result = source.get_citation_relations("seed", "both", rows=5)

    assert result["references"][0]["semantic_scholar_id"] == "cited"
    assert result["cited_by"][0]["semantic_scholar_id"] == "citing"
    assert request.call_args.kwargs["params"]["limit"] == 5
