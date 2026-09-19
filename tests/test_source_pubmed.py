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


def test_parse_article_reads_publication_types_from_element_text() -> None:
    # Regression: the comprehension called .strip() on the Element itself
    # instead of its .text, raising AttributeError ('xml.etree.ElementTree
    # .Element' object has no attribute 'strip') for every article that
    # carries a <PublicationType>, so PubMed searches always failed.
    import xml.etree.ElementTree as ET

    from nature_academic_search.sources.pubmed import _parse_article

    article = ET.fromstring(
        """
        <PubmedArticle>
          <MedlineCitation>
            <PMID>42754655</PMID>
            <Article>
              <Journal>
                <Title>J Mol Biol</Title>
                <JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue>
              </Journal>
              <ArticleTitle>Protein folding pathways</ArticleTitle>
              <PublicationTypeList>
                <PublicationType>Journal Article</PublicationType>
                <PublicationType>Research Support, U.S. Gov't, Non-P.H.S.</PublicationType>
              </PublicationTypeList>
            </Article>
          </MedlineCitation>
        </PubmedArticle>
        """
    )

    record = _parse_article(article)

    assert record["pmid"] == "42754655"
    assert record["title"] == "Protein folding pathways"
    assert record["publication_type"] == (
        "Journal Article; Research Support, U.S. Gov't, Non-P.H.S."
    )
