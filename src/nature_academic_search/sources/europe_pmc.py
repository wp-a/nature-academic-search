"""Europe PMC publication adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..config import get_config
from ..errors import DataSourceError
from ..http import request_json

SOURCE_NAME = "europe_pmc"
SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


class EuropePmcSource:
    """Search Europe PMC and resolve PMID/PMCID records."""

    name = SOURCE_NAME

    def search(
        self,
        query: str,
        rows: int = 5,
        *,
        filter_type: str | None = None,
    ) -> dict[str, Any]:
        if not query or not query.strip():
            raise DataSourceError(SOURCE_NAME, "Empty search query")
        config = get_config()
        effective_query = query.strip()
        if filter_type:
            effective_query = f"({effective_query}) AND PUB_TYPE:{filter_type}"
        params = {
            "query": effective_query,
            "pageSize": max(1, min(rows, config.max_rows, 1_000)),
            "format": "json",
            "resultType": "core",
        }
        payload, response_meta = request_json(
            source=SOURCE_NAME,
            method="GET",
            url=SEARCH_URL,
            params=params,
            timeout=config.europe_pmc_timeout,
        )
        results = _result_items(payload)
        return {
            "total": int(payload.get("hitCount") or 0),
            "query": query,
            "source": SOURCE_NAME,
            "source_meta": {"rate_limit": response_meta} if response_meta else {},
            "results": [_normalize_result(item) for item in results],
        }

    def get_by_id(self, identifier: str) -> dict[str, Any]:
        query = _identifier_query(identifier)
        config = get_config()
        payload, _ = request_json(
            source=SOURCE_NAME,
            method="GET",
            url=SEARCH_URL,
            params={
                "query": query,
                "pageSize": 1,
                "format": "json",
                "resultType": "core",
            },
            timeout=config.europe_pmc_timeout,
        )
        results = _result_items(payload)
        if not results:
            raise DataSourceError(SOURCE_NAME, f"Identifier not found: {identifier}")
        return _normalize_result(results[0])

    def get_by_pmid(self, pmid: str) -> dict[str, Any]:
        return self.get_by_id(pmid)

    def get_by_pmcid(self, pmcid: str) -> dict[str, Any]:
        return self.get_by_id(pmcid)


def _result_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise DataSourceError(SOURCE_NAME, "Malformed search response")
    result_list = payload.get("resultList")
    if not isinstance(result_list, dict) or not isinstance(result_list.get("result"), list):
        raise DataSourceError(SOURCE_NAME, "Malformed search response")
    return [item for item in result_list["result"] if isinstance(item, dict)]


def _normalize_result(item: dict[str, Any]) -> dict[str, Any]:
    native_source = str(item.get("source") or "MED").upper()
    native_id = str(item.get("id") or item.get("pmid") or item.get("pmcid") or "")
    source_id = f"{native_source}:{native_id}"
    pmid = _pmid(str(item.get("pmid") or (native_id if native_source == "MED" else "")))
    pmcid = _pmcid(str(item.get("pmcid") or ""))
    publication_type = _publication_type(item.get("pubType"))
    is_preprint = native_source == "PPR" or "preprint" in publication_type.casefold()
    is_open_access = str(item.get("isOpenAccess") or "").upper() == "Y"
    authors = []
    author_list = item.get("authorList")
    if isinstance(author_list, dict):
        for author in author_list.get("author") or []:
            if not isinstance(author, dict):
                continue
            name = str(author.get("fullName") or author.get("collectiveName") or "").strip()
            if name:
                authors.append(name)

    record: dict[str, Any] = {
        "entity_type": "publication",
        "title": str(item.get("title") or ""),
        "authors": authors,
        "year": _year(item.get("pubYear")),
        "publication_date": item.get("firstPublicationDate"),
        "journal": str(item.get("journalTitle") or ""),
        "abstract": str(item.get("abstractText") or ""),
        "doi": _doi(str(item.get("doi") or "")),
        "pmid": pmid,
        "pmcid": pmcid,
        "publication_type": publication_type,
        "is_preprint": is_preprint,
        "is_open_access": is_open_access,
        "fulltext_url": (
            f"https://europepmc.org/articles/{pmcid}"
            if is_open_access and pmcid
            else ""
        ),
        "source": SOURCE_NAME,
        "source_id": source_id,
        "source_url": f"https://europepmc.org/article/{native_source}/{native_id}",
        "source_records": [
            {
                "source": SOURCE_NAME,
                "source_id": source_id,
                "source_url": f"https://europepmc.org/article/{native_source}/{native_id}",
            }
        ],
        "retrieved_at": _utc_now(),
    }
    if item.get("citedByCount") is not None:
        count = int(item["citedByCount"] or 0)
        record.update(
            {
                "citation_count": count,
                "citation_count_source": SOURCE_NAME,
                "citation_counts": {SOURCE_NAME: count},
            }
        )
    return record


def _identifier_query(identifier: str) -> str:
    value = identifier.strip().upper()
    if value.startswith("PMID:"):
        value = value[5:].strip()
    if re.fullmatch(r"\d{7,8}", value):
        return f"EXT_ID:{value} AND SRC:MED"
    pmcid = _pmcid(value)
    if pmcid:
        return f"PMCID:{pmcid}"
    raise DataSourceError(SOURCE_NAME, f"Invalid PMID/PMCID: {identifier}")


def _pmid(value: str) -> str:
    match = re.fullmatch(r"\d{7,8}", value.strip())
    return match.group(0) if match else ""


def _pmcid(value: str) -> str:
    match = re.search(r"PMC\d+", value, flags=re.IGNORECASE)
    return match.group(0).upper() if match else ""


def _doi(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", "", normalized)
    return normalized.rstrip(". ")


def _year(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _publication_type(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if item)
    return str(value or "")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
