"""Academic search MCP server.

Unified entry point exposing four tools:
  - search_papers: multi-source concurrent search
  - get_paper_by_id: fetch details by supported scholarly identifiers
  - get_citation: formatted citation via CrossRef content negotiation
  - lookup_mesh: MeSH descriptor lookup
"""

from __future__ import annotations

import json
import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import DataSourceError
from .logging import setup_logging
from .search import search_all
from .sources.registry import (
    DEFAULT_PUBLICATION_SOURCES,
    SOURCE_ENTITY_TYPES,
    TRIAL_SOURCES,
    build_adapters,
    source_capabilities,
)
from .verification import verify_record

mcp = FastMCP("academic-search")
logger = setup_logging()

# Singleton source instances (shared across tool calls)
_ADAPTERS = build_adapters(tuple(SOURCE_ENTITY_TYPES))
_crossref = _ADAPTERS["crossref"]
_pubmed = _ADAPTERS["pubmed"]
_arxiv = _ADAPTERS["arxiv"]
_openalex = _ADAPTERS["openalex"]
_europe_pmc = _ADAPTERS["europe_pmc"]
_semantic_scholar = _ADAPTERS["semantic_scholar"]
_clinicaltrials = _ADAPTERS["clinicaltrials_gov"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_id_type(id: str) -> str:
    """Auto-detect identifier type.

    Raw Semantic Scholar paper IDs remain explicit-only because their format is
    not sufficiently distinctive for safe auto-detection.
    Raises ValueError when detection fails.
    """
    id = id.strip()
    if re.match(
        r"^https?://(?:www\.|api\.)?semanticscholar\.org/",
        id,
        flags=re.IGNORECASE,
    ):
        return "semantic_scholar"
    if re.search(r"(?:^|/)NCT\d{8}(?:/?$|[?#])", id, flags=re.IGNORECASE):
        return "nct"
    if re.search(r"(?:^|/)PMC\d+(?:/?$|[?#])", id, flags=re.IGNORECASE):
        return "pmcid"
    if re.search(r"(?:^|/)W\d+(?:/?$|[?#])", id, flags=re.IGNORECASE):
        return "openalex"
    id = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", id, flags=re.IGNORECASE)
    if id.lower().startswith("doi:"):
        id = id[4:].strip()
    if id.startswith("10.") and "/" in id:
        return "doi"
    if id.upper().startswith("PMID:"):
        id = id[5:].strip()
    if re.match(r"^\d{7,8}$", id):
        return "pmid"
    id = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", id, flags=re.IGNORECASE)
    id = id.removesuffix(".pdf")
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", id):
        return "arxiv"
    raise ValueError(f"Cannot detect ID type for: {id}")


def _resolve_id_type(id: str, id_type: str) -> str:
    """Resolve the effective ID type.

    If id_type is "auto", delegate to _detect_id_type.
    Otherwise normalise the explicit type string.
    """
    if id_type == "auto":
        return detect_id_type(id)
    normalised = id_type.lower().strip()
    if normalised in (
        "doi",
        "pmid",
        "pmcid",
        "arxiv",
        "openalex",
        "semantic_scholar",
        "nct",
    ):
        return normalised
    raise ValueError(f"Unsupported id_type: {id_type}")


def _json_ok(data: Any) -> str:
    """Serialize a successful result to JSON string."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def _json_error(message: str, source: str | None = None) -> str:
    """Serialize an error result to JSON string."""
    payload: dict[str, Any] = {"error": message}
    if source:
        payload["source"] = source
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_papers(
    query: str,
    sources: list[str] | None = None,
    rows: int = 5,
    type: str | None = None,
    entity_type: str = "publication",
    enrich: list[str] | None = None,
    filters: dict[str, Any] | None = None,
    ranking: str | None = None,
) -> str:
    """Search publications or trial registrations across supported sources.

    Args:
        query: Search keywords or query string.
        sources: Source names to query. Uses entity-specific defaults when omitted.
        rows: Number of results per source (max 50).
        type: Optional CrossRef work type filter (e.g. "journal-article").
        entity_type: "publication" (default) or "trial".
        enrich: Optional publication enrichers, currently "semantic_scholar".
        filters: Optional normalized discovery filters for date, language, author,
            document type, or identifiers.
        ranking: Optional deterministic ranking mode: "relevance" or "none".

    Returns:
        JSON string with total count, merged results, and any per-source errors.
    """
    if not query or not query.strip():
        return _json_error("Empty search query")

    if entity_type not in {"publication", "trial"}:
        return _json_error(f"Invalid entity_type: {entity_type}")

    if filters is not None and not isinstance(filters, dict):
        return _json_error("filters must be an object")
    if ranking not in {None, "relevance", "none"}:
        return _json_error("ranking must be 'relevance' or 'none'")

    enrich = list(enrich or [])
    valid_sources = {
        source
        for source, source_entity_type in SOURCE_ENTITY_TYPES.items()
        if source_entity_type == entity_type
    }
    invalid = [source for source in (sources or []) if source not in valid_sources]
    if invalid:
        return _json_error(f"Invalid sources: {invalid}. Valid: {sorted(valid_sources)}")
    invalid_enrichers = [
        source
        for source in enrich
        if source not in SOURCE_ENTITY_TYPES
        or "enrich" not in source_capabilities(source)
    ]
    if invalid_enrichers:
        return _json_error(
            f"Invalid enrichers: {invalid_enrichers}. Valid: ['semantic_scholar']"
        )
    if entity_type != "publication" and enrich:
        return _json_error("Trial records do not support publication enrichment")

    rows = max(1, min(rows, 50))

    default_sources = (
        DEFAULT_PUBLICATION_SOURCES if entity_type == "publication" else TRIAL_SOURCES
    )
    adapter_names = list(dict.fromkeys([*(sources or default_sources), *enrich]))
    adapters = {source: _ADAPTERS[source] for source in adapter_names}

    logger.info("search_papers called", extra={
        "tool": "search_papers",
        "query": query,
        "sources": sources,
        "rows": rows,
        "entity_type": entity_type,
        "enrich": enrich,
        "filters": filters,
        "ranking": ranking,
    })

    try:
        import asyncio

        result = asyncio.run(
            search_all(
                query,
                sources,
                rows,
                filter_type=type,
                adapters=adapters,
                enrichers=enrich,
                entity_type=entity_type,
                filters=filters,
                ranking=ranking,
            )
        )
    except Exception as exc:
        logger.exception("search_papers failed")
        return _json_error(f"Search failed: {exc}")

    return _json_ok(result)


@mcp.tool()
def get_paper_by_id(
    id: str,
    id_type: str = "auto",
    expected: dict[str, Any] | None = None,
) -> str:
    """Get publication or trial details by a supported identifier.

    Args:
        id: Paper identifier. Auto-detected if id_type is "auto":
            - Starts with "10." -> DOI (CrossRef)
            - 7-8 digit number -> PMID (PubMed)
            - YYMM.NNNNN format -> arXiv ID (arXiv)
            - PMC..., W..., NCT..., and supported source URLs
        id_type: Force a supported identifier type, or use "auto".
        expected: Optional citation or trial metadata to compare field by field
            after the identifier lookup.

    Returns:
        JSON string with detailed paper metadata.
    """
    if not id or not id.strip():
        return _json_error("Empty identifier")
    if expected is not None and not isinstance(expected, dict):
        return _json_error("Expected metadata must be an object")

    try:
        resolved_type = _resolve_id_type(id, id_type)
    except ValueError as exc:
        return _json_error(str(exc))

    logger.info("get_paper_by_id called", extra={
        "tool": "get_paper_by_id",
        "id": id,
        "id_type": resolved_type,
    })

    try:
        result = _lookup_record(id.strip(), resolved_type)
        if expected is not None:
            result = dict(result)
            result["verification"] = verify_record(expected, result)
    except DataSourceError as exc:
        logger.error("get_paper_by_id failed: %s", exc)
        if expected is not None and "not found" in str(exc).casefold():
            return _json_ok(
                {
                    "id": id,
                    "verification": verify_record(expected, None),
                }
            )
        return _json_error(str(exc), source=exc.source)
    except Exception as exc:
        logger.exception("get_paper_by_id failed unexpectedly")
        return _json_error(f"Unexpected error: {exc}")

    return _json_ok(result)


@mcp.tool()
def get_citation(id: str, id_type: str = "auto", style: str = "apa") -> str:
    """Get formatted citation for a paper.

    Uses CrossRef content negotiation for DOI-based citations.
    For PMID/arXiv IDs, fetches metadata first then generates a basic citation.

    Args:
        id: Supported paper identifier.
        id_type: Force a supported identifier type, or use "auto".
        style: Citation style. Supported: apa, nature, ieee, harvard,
               vancouver, chicago, mla.

    Returns:
        JSON string with the formatted citation.
    """
    if not id or not id.strip():
        return _json_error("Empty identifier")

    try:
        resolved_type = _resolve_id_type(id, id_type)
    except ValueError as exc:
        return _json_error(str(exc))

    logger.info("get_citation called", extra={
        "tool": "get_citation",
        "id": id,
        "id_type": resolved_type,
        "style": style,
    })

    try:
        lookup_id = _normalize_identifier(id, resolved_type)
        if resolved_type == "nct":
            return _json_error(
                "Trial registrations are not paper citations",
                source="clinicaltrials_gov",
            )
        if resolved_type == "doi":
            citation = _crossref.get_citation(lookup_id, style=style)
            return _json_ok({"id": id, "style": style, "citation": citation})

        paper = _lookup_record(lookup_id, resolved_type)
        doi = str(paper.get("doi") or "").strip()
        if doi:
            citation = _crossref.get_citation(doi, style=style)
            return _json_ok({"id": id, "style": style, "citation": citation})

        citation = _format_basic_citation(paper, style)
        return _json_ok(
            {
                "id": id,
                "style": style,
                "citation": citation,
                "metadata_source": paper.get("source"),
            }
        )

    except DataSourceError as exc:
        logger.error("get_citation failed: %s", exc)
        return _json_error(str(exc), source=exc.source)
    except Exception as exc:
        logger.exception("get_citation failed unexpectedly")
        return _json_error(f"Unexpected error: {exc}")


def _lookup_record(identifier: str, id_type: str) -> dict[str, Any]:
    """Route a normalized identifier type to its owning source adapter."""
    identifier = _normalize_identifier(identifier, id_type)
    if id_type == "doi":
        return _crossref.get_by_doi(identifier)
    if id_type == "pmid":
        return _pubmed.get_by_pmid(identifier)
    if id_type == "pmcid":
        return _europe_pmc.get_by_pmcid(identifier)
    if id_type == "arxiv":
        return _arxiv.get_by_id(identifier)
    if id_type == "openalex":
        return _openalex.get_by_id(identifier)
    if id_type == "semantic_scholar":
        return _semantic_scholar.get_by_id(identifier)
    if id_type == "nct":
        return _clinicaltrials.get_by_id(identifier)
    raise ValueError(f"Unsupported ID type: {id_type}")


def _normalize_identifier(identifier: str, id_type: str) -> str:
    """Remove accepted DOI/PMID wrappers before strict source lookups."""
    value = identifier.strip()
    if id_type == "doi":
        value = re.sub(
            r"^https?://(?:dx\.)?doi\.org/",
            "",
            value,
            flags=re.IGNORECASE,
        )
        return re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    if id_type == "pmid":
        return re.sub(r"^pmid:\s*", "", value, flags=re.IGNORECASE)
    return value


def _format_basic_citation(paper: dict, style: str) -> str:
    """Generate a basic citation string from unified paper metadata.

    This is a fallback for non-DOI papers where CrossRef content
    negotiation is not available.
    """
    authors = paper.get("authors", [])
    title = paper.get("title", "Untitled")
    year = paper.get("year", "n.d.")
    journal = paper.get("journal", "")
    doi = paper.get("doi", "")
    arxiv_id = paper.get("arxiv_id", "")
    pmid = paper.get("pmid", "")

    # Author formatting
    if len(authors) > 3:
        author_str = f"{authors[0]} et al."
    elif authors:
        author_str = ", ".join(authors)
    else:
        author_str = "Unknown"

    if style == "nature":
        parts = [f"{author_str}. {title}."]
        if journal:
            parts.append(f" *{journal}*.")
        if year:
            parts.append(f" ({year}).")
        if doi:
            parts.append(f" https://doi.org/{doi}")
        return "".join(parts)

    if style == "ieee":
        ref = f"{author_str}, \"{title}\""
        if journal:
            ref += f", *{journal}*"
        if year:
            ref += f", {year}"
        ref += "."
        if doi:
            ref += f" doi: {doi}."
        return ref

    # Default APA-like
    parts = [f"{author_str} ({year}). {title}."]
    if journal:
        parts.append(f" *{journal}*.")
    if doi:
        parts.append(f" https://doi.org/{doi}")
    elif arxiv_id:
        parts.append(f" arXiv:{arxiv_id}")
    elif pmid:
        parts.append(f" PMID:{pmid}")
    return "".join(parts)


@mcp.tool()
def lookup_mesh(term: str) -> str:
    """Lookup MeSH (Medical Subject Headings) terms.

    Queries the MeSH database via NCBI E-utilities to find matching
    descriptor names and unique IDs.

    Args:
        term: Search term to look up in the MeSH vocabulary.

    Returns:
        JSON string with matching MeSH descriptors.
    """
    if not term or not term.strip():
        return _json_error("Empty MeSH lookup term")

    logger.info("lookup_mesh called", extra={
        "tool": "lookup_mesh",
        "term": term,
    })

    try:
        result = _pubmed.lookup_mesh(term.strip())
    except DataSourceError as exc:
        logger.error("lookup_mesh failed: %s", exc)
        return _json_error(str(exc), source=exc.source)
    except Exception as exc:
        logger.exception("lookup_mesh failed unexpectedly")
        return _json_error(f"Unexpected error: {exc}")

    return _json_ok(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
