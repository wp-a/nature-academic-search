"""Canonical source identities and entity boundaries."""

from __future__ import annotations

DEFAULT_PUBLICATION_SOURCES = (
    "crossref",
    "pubmed",
    "arxiv",
    "openalex",
    "europe_pmc",
)
OPTIONAL_PUBLICATION_SOURCES = ("semantic_scholar",)
TRIAL_SOURCES = ("clinicaltrials_gov",)

SOURCE_ENTITY_TYPES = {
    source: "publication"
    for source in (*DEFAULT_PUBLICATION_SOURCES, *OPTIONAL_PUBLICATION_SOURCES)
}
SOURCE_ENTITY_TYPES.update({source: "trial" for source in TRIAL_SOURCES})

SOURCE_CAPABILITIES = {
    "crossref": frozenset({"search", "lookup", "type_filter", "citation"}),
    "pubmed": frozenset({"search", "lookup", "mesh"}),
    "arxiv": frozenset({"search", "lookup"}),
    "openalex": frozenset({"search", "lookup", "type_filter"}),
    "europe_pmc": frozenset({"search", "lookup", "type_filter"}),
    "semantic_scholar": frozenset({"search", "lookup", "enrich"}),
    "clinicaltrials_gov": frozenset({"search", "lookup"}),
}

SOURCE_TYPE_FILTER_DIALECTS = {
    "crossref": "crossref",
    "openalex": "openalex",
    "europe_pmc": "europe_pmc",
}


def source_capabilities(source: str) -> frozenset[str]:
    try:
        return SOURCE_CAPABILITIES[source]
    except KeyError as exc:
        raise ValueError(f"Unknown academic source: {source}") from exc


def source_type_filter_dialect(source: str) -> str | None:
    """Return the source-native publication type vocabulary, if supported."""
    return SOURCE_TYPE_FILTER_DIALECTS.get(source)


def build_adapters(sources: list[str] | tuple[str, ...]) -> dict[str, object]:
    """Construct only the selected adapters to keep optional sources lazy."""
    from . import (
        ArxivSource,
        ClinicalTrialsSource,
        CrossRefSource,
        EuropePmcSource,
        OpenAlexSource,
        PubMedSource,
        SemanticScholarSource,
    )

    factories = {
        "crossref": CrossRefSource,
        "pubmed": PubMedSource,
        "arxiv": ArxivSource,
        "clinicaltrials_gov": ClinicalTrialsSource,
        "openalex": OpenAlexSource,
        "europe_pmc": EuropePmcSource,
        "semantic_scholar": SemanticScholarSource,
    }
    unknown = [source for source in sources if source not in factories]
    if unknown:
        raise ValueError(f"Adapters are not available for: {unknown}")
    return {source: factories[source]() for source in sources}
