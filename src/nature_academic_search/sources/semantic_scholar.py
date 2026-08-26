"""Semantic Scholar Academic Graph adapter."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any

from ..config import get_config
from ..errors import DataSourceError
from ..http import request_json

SOURCE_NAME = "semantic_scholar"
BASE_URL = "https://api.semanticscholar.org/graph/v1"
REQUEST_INTERVAL_SECONDS = 1.0
FIELDS = ",".join(
    (
        "paperId",
        "externalIds",
        "title",
        "abstract",
        "year",
        "venue",
        "authors",
        "citationCount",
        "referenceCount",
        "url",
        "openAccessPdf",
    )
)
RELATION_CAPABILITIES = frozenset({"references", "cited_by"})
RELATION_FIELDS = f"{FIELDS},citations,references"


class SemanticScholarSource:
    """Search and resolve papers through the Academic Graph API."""

    name = SOURCE_NAME
    RELATION_CAPABILITIES = RELATION_CAPABILITIES

    def __init__(self) -> None:
        self._last_request_at: float | None = None

    def search(self, query: str, rows: int = 5) -> dict[str, Any]:
        if not query or not query.strip():
            raise DataSourceError(SOURCE_NAME, "Empty search query")
        config = get_config()
        payload, response_meta = self._request(
            url=f"{BASE_URL}/paper/search",
            params={
                "query": query.strip(),
                "limit": max(1, min(rows, config.max_rows, 100)),
                "fields": FIELDS,
            },
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise DataSourceError(SOURCE_NAME, "Malformed search response")
        return {
            "total": int(payload.get("total") or 0),
            "query": query,
            "source": SOURCE_NAME,
            "source_meta": {"rate_limit": response_meta} if response_meta else {},
            "results": [
                _normalize_paper(paper)
                for paper in payload["data"]
                if isinstance(paper, dict)
            ],
        }

    def get_by_id(self, identifier: str) -> dict[str, Any]:
        normalized = _lookup_identifier(identifier)
        payload, _ = self._request(
            url=f"{BASE_URL}/paper/{normalized}",
            params={"fields": FIELDS},
        )
        if not isinstance(payload, dict):
            raise DataSourceError(SOURCE_NAME, "Malformed paper response")
        return _normalize_paper(payload)

    def get_citation_relations(
        self, identifier: str, relation: str = "both", rows: int = 20
    ) -> dict[str, list[dict[str, Any]]]:
        try:
            normalized = _lookup_identifier(identifier)
        except DataSourceError:
            # API-native opaque IDs are accepted for relation expansion.
            normalized = str(identifier).strip()
            if not normalized:
                raise
        config = get_config()
        payload, _ = self._request(
            url=f"{BASE_URL}/paper/{normalized}",
            params={
                "fields": RELATION_FIELDS,
                "limit": max(1, min(rows, config.max_rows, 100)),
            },
        )
        if not isinstance(payload, dict):
            raise DataSourceError(SOURCE_NAME, "Malformed relation response")
        result: dict[str, list[dict[str, Any]]] = {"references": [], "cited_by": []}
        if relation in {"references", "both"}:
            result["references"] = [
                _normalize_paper(item)
                for item in (payload.get("references") or [])[:rows]
                if isinstance(item, dict)
            ]
        if relation in {"cited_by", "both"}:
            result["cited_by"] = [
                _normalize_paper(item)
                for item in (payload.get("citations") or [])[:rows]
                if isinstance(item, dict)
            ]
        return result

    def _request(
        self,
        *,
        url: str,
        params: dict[str, Any],
    ) -> tuple[Any, dict[str, str]]:
        self._throttle()
        config = get_config()
        headers = (
            {"x-api-key": config.semantic_scholar_api_key}
            if config.semantic_scholar_api_key
            else {}
        )
        return request_json(
            source=SOURCE_NAME,
            method="GET",
            url=url,
            params=params,
            headers=headers,
            timeout=config.semantic_scholar_timeout,
        )

    def _throttle(self) -> None:
        now = time.monotonic()
        if self._last_request_at is None:
            self._last_request_at = now
            return
        elapsed = now - self._last_request_at
        wait = max(0.0, REQUEST_INTERVAL_SECONDS - elapsed)
        if wait:
            time.sleep(wait)
        self._last_request_at = now + wait


def _normalize_paper(paper: dict[str, Any]) -> dict[str, Any]:
    paper_id = str(paper.get("paperId") or "")
    external_ids = (
        paper.get("externalIds")
        if isinstance(paper.get("externalIds"), dict)
        else {}
    )
    authors = [
        str(author.get("name") or "").strip()
        for author in paper.get("authors") or []
        if isinstance(author, dict) and str(author.get("name") or "").strip()
    ]
    open_pdf = (
        paper.get("openAccessPdf")
        if isinstance(paper.get("openAccessPdf"), dict)
        else {}
    )
    citation_count = int(paper.get("citationCount") or 0)
    reference_count = int(paper.get("referenceCount") or 0)
    source_url = str(
        paper.get("url")
        or f"https://www.semanticscholar.org/paper/{paper_id}"
    )
    return {
        "entity_type": "publication",
        "title": str(paper.get("title") or ""),
        "authors": authors,
        "year": paper.get("year"),
        "journal": str(paper.get("venue") or ""),
        "abstract": str(paper.get("abstract") or ""),
        "doi": _normalize_doi(str(external_ids.get("DOI") or "")),
        "pmid": str(external_ids.get("PubMed") or "").strip(),
        "arxiv_id": _normalize_arxiv(str(external_ids.get("ArXiv") or "")),
        "semantic_scholar_id": paper_id,
        "citation_count": citation_count,
        "citation_count_source": SOURCE_NAME,
        "citation_counts": {SOURCE_NAME: citation_count},
        "reference_count": reference_count,
        "reference_count_source": SOURCE_NAME,
        "is_open_access": bool(open_pdf.get("url")),
        "fulltext_url": str(open_pdf.get("url") or ""),
        "source": SOURCE_NAME,
        "source_id": paper_id,
        "source_url": source_url,
        "source_records": [
            {
                "source": SOURCE_NAME,
                "source_id": paper_id,
                "source_url": source_url,
            }
        ],
        "retrieved_at": _utc_now(),
    }


def _lookup_identifier(identifier: str) -> str:
    value = identifier.strip()
    if not value:
        raise DataSourceError(SOURCE_NAME, "Empty paper identifier")
    if "semanticscholar.org/paper/" in value.casefold():
        return value.rstrip("/").rsplit("/", 1)[-1]
    upper = value.upper()
    if upper.startswith(("DOI:", "ARXIV:", "PMID:")):
        prefix, raw = value.split(":", 1)
        return f"{prefix.upper()}:{raw.strip()}"
    if value.startswith("10.") and "/" in value:
        return f"DOI:{value}"
    if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", value):
        return f"ARXIV:{value}"
    if re.fullmatch(r"[0-9a-fA-F]{40}", value):
        return value
    raise DataSourceError(SOURCE_NAME, f"Invalid paper identifier: {identifier}")


def _normalize_doi(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", "", normalized)
    return normalized.rstrip(". ")


def _normalize_arxiv(value: str) -> str:
    normalized = value.strip()
    return re.sub(r"v\d+$", "", normalized)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
