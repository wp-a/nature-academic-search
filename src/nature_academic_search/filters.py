"""Normalized discovery filters and source-specific query translation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

FILTER_FIELDS = frozenset(
    {"date_from", "date_to", "language", "author", "document_type", "identifiers"}
)


def normalize_filters(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate and canonicalize the public discovery filter object."""
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError("filters must be an object")

    unknown = sorted(set(raw) - FILTER_FIELDS)
    if unknown:
        raise ValueError(f"Unknown filter field(s): {', '.join(unknown)}")

    normalized: dict[str, Any] = {}
    for field in ("date_from", "date_to"):
        if raw.get(field) not in (None, ""):
            value = str(raw[field]).strip()
            _parse_date(value, field)
            normalized[field] = value
    if normalized.get("date_from") and normalized.get("date_to"):
        if normalized["date_from"] > normalized["date_to"]:
            raise ValueError("date_from must be on or before date_to")

    if raw.get("language") not in (None, ""):
        language = str(raw["language"]).strip().casefold()
        if not re.fullmatch(r"[a-z]{2,3}", language):
            raise ValueError("language must be a two- or three-letter code")
        normalized["language"] = language

    if raw.get("author") not in (None, ""):
        author = str(raw["author"]).strip()
        if not author:
            raise ValueError("author must not be empty")
        normalized["author"] = author

    if raw.get("document_type") not in (None, "", []):
        normalized["document_type"] = _string_list(raw["document_type"], "document_type")

    if raw.get("identifiers") not in (None, "", []):
        normalized["identifiers"] = [
            _normalize_identifier(value)
            for value in _string_list(raw["identifiers"], "identifiers")
        ]

    return normalized


def translate_filters(source: str, filters: Mapping[str, Any]) -> dict[str, Any]:
    """Translate normalized filters into adapter kwargs and deferred fields."""
    normalized = normalize_filters(filters)
    kwargs: dict[str, Any] = {}
    query_parts: list[str] = []
    applied: list[str] = []
    post_filter: list[str] = []

    if source == "crossref":
        for field in ("date_from", "date_to", "author"):
            if field in normalized:
                kwargs[field] = normalized[field]
                applied.append(field)
        if "document_type" in normalized:
            kwargs["document_type"] = normalized["document_type"]
            applied.append("document_type")
        post_filter.extend(field for field in ("language", "identifiers") if field in normalized)
    elif source == "pubmed":
        if "date_from" in normalized or "date_to" in normalized:
            start = normalized.get("date_from", "0000-01-01").replace("-", "/")
            end = normalized.get("date_to", "3000-12-31").replace("-", "/")
            query_parts.append(f'("{start}"[Date - Publication] : "{end}"[Date - Publication])')
            applied.append("date_from" if "date_from" in normalized else "date_to")
        if "author" in normalized:
            query_parts.append(f'{normalized["author"]}[Author]')
            applied.append("author")
        if "language" in normalized:
            query_parts.append(f'{normalized["language"]}[Language]')
            applied.append("language")
        if "document_type" in normalized:
            query_parts.append(
                " OR ".join(f'"{value}"[Publication Type]' for value in normalized["document_type"])
            )
            applied.append("document_type")
        if "identifiers" in normalized:
            post_filter.append("identifiers")
    elif source == "openalex":
        for field in ("date_from", "date_to", "language", "author"):
            if field in normalized:
                kwargs[field] = normalized[field]
                applied.append(field)
        if "document_type" in normalized:
            kwargs["document_type"] = normalized["document_type"]
            applied.append("document_type")
        if "identifiers" in normalized:
            post_filter.append("identifiers")
    elif source == "europe_pmc":
        for field in ("date_from", "date_to", "language", "author", "document_type"):
            if field in normalized:
                kwargs[field] = normalized[field]
                applied.append(field)
        if "identifiers" in normalized:
            post_filter.append("identifiers")
    elif source == "arxiv":
        for field in ("date_from", "date_to"):
            if field in normalized:
                kwargs[field] = normalized[field]
                applied.append(field)
        post_filter.extend(
            field
            for field in ("language", "author", "document_type", "identifiers")
            if field in normalized
        )
    else:
        post_filter.extend(normalized)

    return {
        "kwargs": kwargs,
        "query": " AND ".join(query_parts),
        "applied": applied,
        "post_filter": post_filter,
    }


def apply_post_filters(
    records: Sequence[Mapping[str, Any]], filters: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Apply strict local filtering for fields that source APIs may omit."""
    normalized = normalize_filters(filters)
    return [dict(record) for record in records if _matches(record, normalized)]


def _matches(record: Mapping[str, Any], filters: Mapping[str, Any]) -> bool:
    if "date_from" in filters or "date_to" in filters:
        value = record.get("publication_date") or record.get("date") or record.get("start_date")
        if value:
            candidate = str(value)[:10]
        elif record.get("year") not in (None, ""):
            try:
                candidate = f"{int(record['year']):04d}-01-01"
            except (TypeError, ValueError):
                return False
        else:
            return False
        if filters.get("date_from") and candidate < filters["date_from"]:
            return False
        if filters.get("date_to") and candidate > filters["date_to"]:
            return False

    if "language" in filters:
        language = str(record.get("language") or record.get("lang") or "").casefold()
        if language not in _language_aliases(filters["language"]):
            return False

    if "author" in filters:
        authors = record.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        needle = str(filters["author"]).casefold()
        if not any(needle in str(author).casefold() for author in authors):
            return False

    if "document_type" in filters:
        value = str(
            record.get("document_type")
            or record.get("publication_type")
            or record.get("type")
            or record.get("study_type")
            or ""
        ).casefold()
        if not any(option.casefold() in value for option in filters["document_type"]):
            return False

    if "identifiers" in filters:
        record_identifiers = {
            _normalize_identifier(str(record[field]))
            for field in (
                "doi",
                "pmid",
                "pmcid",
                "arxiv_id",
                "openalex_id",
                "semantic_scholar_id",
                "nct_id",
            )
            if record.get(field)
        }
        if not record_identifiers.intersection(filters["identifiers"]):
            return False

    return True


def _string_list(value: Any, field: str) -> list[str]:
    values = (
        [value]
        if isinstance(value, str)
        else list(value)
        if isinstance(value, Sequence)
        else None
    )
    if values is None or not values or any(not str(item).strip() for item in values):
        raise ValueError(f"{field} must be a string or non-empty list of strings")
    result: list[str] = []
    for item in values:
        cleaned = str(item).strip()
        if cleaned.casefold() not in {value.casefold() for value in result}:
            result.append(cleaned.casefold() if field == "document_type" else cleaned)
    return result


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD") from exc


def _normalize_identifier(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", "", normalized, flags=re.I)
    normalized = normalized.rstrip(". ")
    if normalized.casefold().startswith(("10.", "doi:")):
        return normalized.casefold()
    if re.fullmatch(r"\d{7,8}", normalized):
        return normalized
    if re.match(r"^(?:pmc|nct)", normalized, flags=re.I):
        return normalized.upper()
    return normalized.casefold()


def _language_aliases(language: str) -> set[str]:
    aliases = {language.casefold()}
    aliases.update({"en", "eng"} if language in {"en", "eng"} else set())
    aliases.update({"zh", "chi", "zho"} if language in {"zh", "chi", "zho"} else set())
    return aliases
