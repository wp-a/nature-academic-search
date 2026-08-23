from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


def test_crossref_translates_date_author_and_document_type_to_api_params() -> None:
    from nature_academic_search.sources.crossref import CrossRefSource

    source = CrossRefSource()
    with patch.object(
        source,
        "_request",
        return_value={"total-results": 0, "items": []},
    ) as request:
        source.search(
            "AI",
            date_from="2024-01-01",
            date_to="2024-12-31",
            author="Jane Doe",
            document_type=["journal-article"],
        )

    params = request.call_args.kwargs["params"]
    assert params["query.author"] == "Jane Doe"
    assert params["filter"] == (
        "type:journal-article,from-pub-date:2024-01-01,until-pub-date:2024-12-31"
    )


def test_openalex_translates_normalized_filters_to_filter_expression() -> None:
    from nature_academic_search.sources.openalex import OpenAlexSource

    config = SimpleNamespace(openalex_api_key="", openalex_timeout=10, max_rows=50)
    payload = {"meta": {"count": 0}, "results": []}
    with (
        patch("nature_academic_search.sources.openalex.get_config", return_value=config),
        patch(
            "nature_academic_search.sources.openalex.request_json",
            return_value=(payload, {}),
        ) as request,
    ):
        OpenAlexSource().search(
            "AI",
            date_from="2024-01-01",
            date_to="2024-12-31",
            language="en",
            author="Jane Doe",
            document_type=["article"],
        )

    assert request.call_args.kwargs["params"]["filter"] == (
        "from_publication_date:2024-01-01,to_publication_date:2024-12-31,"
        "language:en,author.search:Jane Doe,type:article"
    )


def test_europe_pmc_translates_filters_without_changing_unfiltered_query() -> None:
    from nature_academic_search.sources.europe_pmc import EuropePmcSource

    config = SimpleNamespace(europe_pmc_timeout=10, max_rows=50)
    payload = {"hitCount": 0, "resultList": {"result": []}}
    with (
        patch("nature_academic_search.sources.europe_pmc.get_config", return_value=config),
        patch(
            "nature_academic_search.sources.europe_pmc.request_json",
            return_value=(payload, {}),
        ) as request,
    ):
        source = EuropePmcSource()
        source.search("AI")
        assert request.call_args.kwargs["params"]["query"] == "AI"
        source.search("AI", date_from="2024-01-01", language="en")

    translated = request.call_args.kwargs["params"]["query"]
    assert "FIRST_PDATE:[2024-01-01 TO 3000-12-31]" in translated
    assert "LANGUAGE:en" in translated
