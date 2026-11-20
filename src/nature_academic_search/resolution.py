"""Route scholarly identifiers to their source adapters."""

from __future__ import annotations

import re
from functools import cache
from typing import Any

from .sources.registry import SOURCE_ENTITY_TYPES, build_adapters

_LOOKUP_METHODS = {
    "doi": ("crossref", "get_by_doi"),
    "pmid": ("pubmed", "get_by_pmid"),
    "pmcid": ("europe_pmc", "get_by_pmcid"),
    "arxiv": ("arxiv", "get_by_id"),
    "openalex": ("openalex", "get_by_id"),
    "semantic_scholar": ("semantic_scholar", "get_by_id"),
    "nct": ("clinicaltrials_gov", "get_by_id"),
}


@cache
def runtime_adapters() -> dict[str, object]:
    return build_adapters(tuple(SOURCE_ENTITY_TYPES))


def resolve_record(identifier: str, id_type: str) -> dict[str, Any]:
    """Look up a record by a resolved identifier type."""
    try:
        source, method = _LOOKUP_METHODS[id_type]
    except KeyError:
        raise ValueError(f"Unsupported ID type: {id_type}") from None
    adapter = runtime_adapters()[source]
    return getattr(adapter, method)(normalize_identifier(identifier, id_type))


def normalize_identifier(identifier: str, id_type: str) -> str:
    """Remove accepted DOI and PMID wrappers before source lookups."""
    value = identifier.strip()
    if id_type == "doi":
        value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
        return re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    if id_type == "pmid":
        return re.sub(r"^pmid:\s*", "", value, flags=re.IGNORECASE)
    return value
