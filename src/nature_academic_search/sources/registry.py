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
