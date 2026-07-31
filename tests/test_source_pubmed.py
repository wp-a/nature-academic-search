from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


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
