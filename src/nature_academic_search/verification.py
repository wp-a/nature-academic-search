"""Field-level comparison for identifier-resolved research records."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

_PUBLICATION_FIELDS = {
    "title",
    "authors",
    "year",
    "journal",
    "doi",
    "pmid",
    "pmcid",
    "arxiv_id",
    "openalex_id",
    "semantic_scholar_id",
}
_TRIAL_FIELDS = {
    "nct_id",
    "title",
    "status",
    "sponsor",
    "start_date",
    "completion_date",
}
_FIELD_ALIASES = {"status": "overall_status"}
_IDENTIFIER_FIELDS = {
    "doi",
    "pmid",
    "pmcid",
    "arxiv_id",
    "openalex_id",
    "semantic_scholar_id",
    "nct_id",
}


def verify_record(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Compare caller-provided metadata with a resolved source record."""
    if actual is None:
        return {
            "status": "not_found",
            "fields": {},
            "method": "identifier_lookup",
        }

    entity_type = str(actual.get("entity_type") or "publication")
    allowed_fields = _TRIAL_FIELDS if entity_type == "trial" else _PUBLICATION_FIELDS
    fields: dict[str, dict[str, Any]] = {}

    for expected_field, expected_value in expected.items():
        if expected_field in {"entity_type", "record_id"} or expected_value in (
            None,
            "",
            [],
            {},
        ):
            continue
        if expected_field not in allowed_fields:
            fields[expected_field] = {"status": "uncheckable"}
            continue

        actual_field = _FIELD_ALIASES.get(expected_field, expected_field)
        actual_value = actual.get(actual_field)
        if actual_value in (None, "", [], {}):
            fields[expected_field] = {"status": "missing"}
            continue

        if _values_match(expected_field, expected_value, actual_value):
            fields[expected_field] = {"status": "match"}
        else:
            fields[expected_field] = {
                "status": "mismatch",
                "expected": expected_value,
                "actual": actual_value,
            }

    statuses = {field["status"] for field in fields.values()}
    if "mismatch" in statuses:
        status = "mismatch"
    elif not fields or statuses & {"missing", "uncheckable"}:
        status = "manual_needed"
    else:
        status = "verified"

    return {
        "status": status,
        "fields": fields,
        "method": "identifier_lookup",
    }


def _values_match(field: str, expected: Any, actual: Any) -> bool:
    if field == "authors":
        return _authors_match(expected, actual)
    if field == "year":
        return _year_value(expected) == _year_value(actual)
    if field in _IDENTIFIER_FIELDS:
        return _canonical_identifier(field, expected) == _canonical_identifier(field, actual)
    return _normalize_text(expected) == _normalize_text(actual)


def _authors_match(expected: Any, actual: Any) -> bool:
    expected_names = _author_names(expected)
    actual_names = _author_names(actual)
    if not expected_names or not actual_names or len(expected_names) > len(actual_names):
        return False
    return expected_names == actual_names[: len(expected_names)]


def _author_names(value: Any) -> list[str]:
    values = (
        value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
        else [value]
    )
    names: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            item = item.get("name") or item.get("full_name") or item.get("family") or ""
        normalized = _normalize_text(item)
        if normalized:
            names.append(normalized)
    return names


def _year_value(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _canonical_identifier(field: str, value: Any) -> str:
    normalized = str(value or "").strip()
    if field == "doi":
        normalized = re.sub(
            r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)",
            "",
            normalized,
            flags=re.IGNORECASE,
        )
        return normalized.rstrip(". ").casefold()
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
        return re.sub(r"v\d+$", "", normalized.removesuffix(".pdf"))
    if field == "openalex_id":
        normalized = re.sub(r"^https?://openalex\.org/", "", normalized, flags=re.IGNORECASE)
        return normalized.upper()
    if field == "nct_id":
        return normalized.upper()
    return normalized


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(char for char in text if char.isalnum() or char.isspace()).strip()
