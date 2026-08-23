"""OpenAlex works adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..config import get_config
from ..errors import DataSourceError
from ..http import request_json

SOURCE_NAME = "openalex"
BASE_URL = "https://api.openalex.org/works"
SELECT_FIELDS = ",".join(
    (
        "id",
        "doi",
        "display_name",
        "publication_year",
        "publication_date",
        "type",
        "cited_by_count",
        "ids",
        "authorships",
        "abstract_inverted_index",
        "primary_location",
        "open_access",
    )
)


class OpenAlexSource:
    """Search and resolve scholarly works through OpenAlex."""

    name = SOURCE_NAME

    def search(
        self,
        query: str,
        rows: int = 5,
        *,
        filter_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        language: str | None = None,
        author: str | None = None,
        document_type: list[str] | None = None,
    ) -> dict[str, Any]:
        if not query or not query.strip():
            raise DataSourceError(SOURCE_NAME, "Empty search query")

        config = get_config()
        params: dict[str, Any] = {
            "search": query.strip(),
            "per_page": max(1, min(rows, config.max_rows, 100)),
            "select": SELECT_FIELDS,
        }
        filter_parts: list[str] = []
        if filter_type:
            filter_parts.append(f"type:{filter_type}")
        if date_from:
            filter_parts.append(f"from_publication_date:{date_from}")
        if date_to:
            filter_parts.append(f"to_publication_date:{date_to}")
        if language:
            filter_parts.append(f"language:{language}")
        if author:
            filter_parts.append(f"author.search:{author}")
        if document_type:
            filter_parts.append("type:" + "|".join(document_type))
        if filter_parts:
            params["filter"] = ",".join(filter_parts)
        if config.openalex_api_key:
            params["api_key"] = config.openalex_api_key

        payload, response_meta = request_json(
            source=SOURCE_NAME,
            method="GET",
            url=BASE_URL,
            params=params,
            timeout=config.openalex_timeout,
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise DataSourceError(SOURCE_NAME, "Malformed search response")

        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        source_meta: dict[str, Any] = {}
        if meta.get("cost_usd") is not None:
            source_meta["cost_usd"] = meta["cost_usd"]
        if response_meta:
            source_meta["rate_limit"] = response_meta
        return {
            "total": int(meta.get("count") or 0),
            "query": query,
            "source": SOURCE_NAME,
            "source_meta": source_meta,
            "results": [
                _normalize_work(work)
                for work in payload["results"]
                if isinstance(work, dict)
            ],
        }

    def get_by_id(self, identifier: str) -> dict[str, Any]:
        normalized = _lookup_identifier(identifier)
        config = get_config()
        params: dict[str, Any] = {"select": SELECT_FIELDS}
        if config.openalex_api_key:
            params["api_key"] = config.openalex_api_key
        payload, _ = request_json(
            source=SOURCE_NAME,
            method="GET",
            url=f"{BASE_URL}/{normalized}",
            params=params,
            timeout=config.openalex_timeout,
        )
        if not isinstance(payload, dict):
            raise DataSourceError(SOURCE_NAME, "Malformed work response")
        return _normalize_work(payload)


def _normalize_work(work: dict[str, Any]) -> dict[str, Any]:
    source_url = str(work.get("id") or "")
    openalex_id = _openalex_id(source_url)
    ids = work.get("ids") if isinstance(work.get("ids"), dict) else {}
    primary_location = (
        work.get("primary_location")
        if isinstance(work.get("primary_location"), dict)
        else {}
    )
    source = (
        primary_location.get("source")
        if isinstance(primary_location.get("source"), dict)
        else {}
    )
    open_access = (
        work.get("open_access") if isinstance(work.get("open_access"), dict) else {}
    )
    cited_by_count = int(work.get("cited_by_count") or 0)
    authors = []
    for authorship in work.get("authorships") or []:
        if not isinstance(authorship, dict) or not isinstance(authorship.get("author"), dict):
            continue
        name = str(authorship["author"].get("display_name") or "").strip()
        if name:
            authors.append(name)

    return {
        "entity_type": "publication",
        "title": str(work.get("display_name") or work.get("title") or ""),
        "authors": authors,
        "year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "journal": str(source.get("display_name") or ""),
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "doi": _normalize_doi(str(work.get("doi") or ids.get("doi") or "")),
        "pmid": _identifier_digits(str(ids.get("pmid") or ""), "pmid"),
        "pmcid": _identifier_digits(str(ids.get("pmcid") or ""), "pmc"),
        "openalex_id": openalex_id,
        "publication_type": work.get("type"),
        "language": str(work.get("language") or "").casefold(),
        "citation_count": cited_by_count,
        "citation_count_source": SOURCE_NAME,
        "citation_counts": {SOURCE_NAME: cited_by_count},
        "is_open_access": bool(open_access.get("is_oa")),
        "fulltext_url": str(
            open_access.get("oa_url") or primary_location.get("pdf_url") or ""
        ),
        "source": SOURCE_NAME,
        "source_id": openalex_id,
        "source_url": source_url,
        "source_records": [
            {
                "source": SOURCE_NAME,
                "source_id": openalex_id,
                "source_url": source_url,
            }
        ],
        "retrieved_at": _utc_now(),
    }


def _lookup_identifier(identifier: str) -> str:
    value = identifier.strip()
    if not value:
        raise DataSourceError(SOURCE_NAME, "Empty work identifier")
    if value.startswith("10."):
        return f"https://doi.org/{value}"
    return _openalex_id(value)


def _openalex_id(value: str) -> str:
    match = re.search(r"(?:^|/)(W\d+)$", value.strip(), flags=re.IGNORECASE)
    if not match:
        raise DataSourceError(SOURCE_NAME, f"Invalid OpenAlex work identifier: {value}")
    return match.group(1).upper()


def _normalize_doi(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", "", normalized)
    return normalized.rstrip(". ")


def _identifier_digits(value: str, prefix: str) -> str:
    if not value:
        return ""
    if prefix == "pmc":
        match = re.search(r"PMC\d+", value, flags=re.IGNORECASE)
        return match.group(0).upper() if match else ""
    match = re.search(r"(?<!\d)(\d{7,8})(?!\d)", value)
    return match.group(1) if match else ""


def _reconstruct_abstract(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    positions = [
        position
        for indexes in value.values()
        if isinstance(indexes, list)
        for position in indexes
        if isinstance(position, int) and position >= 0
    ]
    if not positions:
        return ""
    words = [""] * (max(positions) + 1)
    for word, indexes in value.items():
        if not isinstance(indexes, list):
            continue
        for position in indexes:
            if isinstance(position, int) and 0 <= position < len(words):
                words[position] = str(word)
    return " ".join(word for word in words if word).strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
