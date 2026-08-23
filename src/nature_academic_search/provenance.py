"""Stable identifiers and secret-free fingerprints for research runs."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

_STRONG_IDENTIFIERS = (
    ("doi", "doi"),
    ("pmid", "pmid"),
    ("pmcid", "pmcid"),
    ("arxiv_id", "arxiv"),
    ("openalex_id", "openalex"),
    ("semantic_scholar_id", "semantic_scholar"),
    ("nct_id", "nct"),
)


def stable_record_id(record: Mapping[str, Any]) -> str:
    """Return a deterministic, namespaced ID for a normalized record."""
    entity_type = _normalize_token(record.get("entity_type") or "publication")

    for field, namespace in _STRONG_IDENTIFIERS:
        value = _canonical_identifier(field, record.get(field))
        if value:
            return f"{entity_type}:{namespace}:{value}"

    fallback = "\x1f".join(
        (
            entity_type,
            _normalize_text(record.get("title")),
            _normalize_token(record.get("year")),
            _normalize_text(_first_author(record)),
        )
    )
    digest = hashlib.sha256(fallback.encode("utf-8")).hexdigest()[:24]
    return f"{entity_type}:sha256:{digest}"


def result_fingerprint(record_ids: Sequence[str]) -> str:
    """Hash ordered record IDs so a search result set can be compared safely."""
    payload = "\n".join(str(record_id) for record_id in record_ids)
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _canonical_identifier(field: str, value: Any) -> str:
    if value in (None, ""):
        return ""
    normalized = str(value).strip()
    if field == "doi":
        normalized = re.sub(
            r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)",
            "",
            normalized,
            flags=re.IGNORECASE,
        )
        return normalized.rstrip(". ").lower()
    if field == "pmid":
        return re.sub(r"^pmid:\s*", "", normalized, flags=re.IGNORECASE)
    if field == "pmcid":
        return re.sub(r"^pmcid:\s*", "", normalized, flags=re.IGNORECASE).upper()
    if field == "arxiv_id":
        normalized = re.sub(
            r"^https?://arxiv\.org/(?:abs|pdf)/",
            "",
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = normalized.removesuffix(".pdf")
        return re.sub(r"v\d+$", "", normalized)
    if field == "openalex_id":
        normalized = re.sub(r"^https?://openalex\.org/", "", normalized, flags=re.IGNORECASE)
        return normalized.upper()
    if field == "nct_id":
        return normalized.upper()
    return normalized


def _first_author(record: Mapping[str, Any]) -> Any:
    authors = record.get("authors")
    if isinstance(authors, Sequence) and not isinstance(authors, (str, bytes)) and authors:
        first = authors[0]
        if isinstance(first, Mapping):
            return first.get("name") or first.get("full_name") or first.get("family") or ""
        return first
    return record.get("first_author") or ""


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(char for char in text if char.isalnum() or char.isspace()).strip()


def _normalize_token(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()
