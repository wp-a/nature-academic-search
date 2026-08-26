"""CrossRef data source for academic search."""

from urllib.parse import quote

import requests

from ..config import get_config
from ..errors import DataSourceError

CROSSREF_API = "https://api.crossref.org"


class CrossRefSource:
    """CrossRef API wrapper with unified result format."""

    SOURCE_NAME = "crossref"
    RELATION_CAPABILITIES = frozenset({"references"})

    def __init__(self):
        config = get_config()
        mailto = config.crossref_mailto or "user@example.com"
        self._headers = {
            "User-Agent": f"ClaudeCode-MCP-Crossref/1.0 (mailto:{mailto})",
        }
        self._timeout = config.crossref_timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        rows: int = 5,
        filter_type: str | None = None,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        author: str | None = None,
        document_type: list[str] | None = None,
    ) -> dict:
        """Search CrossRef works.

        Args:
            query: Keywords, author name, title, DOI prefix, etc.
            rows: Number of results (max 50).
            filter_type: Optional work type filter, e.g. "journal-article".

        Returns:
            {"total": int, "results": [unified_result, ...]}
        """
        params: dict = {"query": query, "rows": min(rows, 50)}
        filter_parts: list[str] = []
        selected_type = filter_type or (document_type[0] if document_type else None)
        if selected_type:
            filter_parts.append(f"type:{selected_type}")
        if date_from:
            filter_parts.append(f"from-pub-date:{date_from}")
        if date_to:
            filter_parts.append(f"until-pub-date:{date_to}")
        if filter_parts:
            params["filter"] = ",".join(filter_parts)
        if author:
            params["query.author"] = author

        data = self._request("/works", params=params)
        items = data.get("items", [])
        total = data.get("total-results", 0)

        results = [self._normalize_search_item(item) for item in items]
        return {"total": total, "results": results}

    def get_by_doi(self, doi: str) -> dict:
        """Get detailed metadata for a single work by DOI.

        Args:
            doi: Digital Object Identifier (e.g. "10.1038/nature12373").

        Returns:
            Unified result dict with extra fields (abstract, volume, etc.).
        """
        data = self._request(f"/works/{quote(doi, safe='/')}")
        return self._normalize_detail_item(data)

    def get_citation(self, doi: str, style: str = "apa") -> str:
        """Return a formatted citation string via CrossRef content negotiation.

        Args:
            doi: Digital Object Identifier.
            style: Citation style (apa, nature, vancouver, ieee, etc.).

        Returns:
            Formatted citation string.
        """
        url = f"{CROSSREF_API}/works/{quote(doi, safe='/')}/transform"
        headers = {
            **self._headers,
            "Accept": f"text/x-bibliography; style={style}",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=self._timeout)
        except requests.RequestException as exc:
            raise DataSourceError(
                self.SOURCE_NAME,
                f"Network error fetching citation for {doi}: {exc}",
                original_error=exc,
            ) from exc

        if resp.status_code == 404:
            return f"Citation not available for DOI: {doi}"
        if resp.status_code == 406:
            raise DataSourceError(
                self.SOURCE_NAME,
                f"Unsupported citation style: {style}",
            )

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise DataSourceError(
                self.SOURCE_NAME,
                f"HTTP {resp.status_code} fetching citation for {doi}",
                original_error=exc,
            ) from exc

        return resp.text.strip()

    def get_citation_relations(
        self, identifier: str, relation: str = "both", rows: int = 20
    ) -> dict[str, list[dict]]:
        """Return references recorded in Crossref metadata.

        Crossref exposes outgoing references on a work, but does not provide a
        portable incoming-citations endpoint.  The latter is intentionally
        returned as an empty list; the graph coordinator records the source
        capability separately.
        """
        result: dict[str, list[dict]] = {"references": [], "cited_by": []}
        if relation not in {"references", "both"}:
            return result
        doi = _normalize_doi(identifier)
        if not doi:
            raise DataSourceError(self.SOURCE_NAME, f"Invalid DOI: {identifier}")
        payload = self._request(f"/works/{quote(doi, safe='/')}")
        references = payload.get("reference") if isinstance(payload, dict) else []
        if not isinstance(references, list):
            return result
        result["references"] = [
            _normalize_reference(item)
            for item in references[: max(1, min(rows, 100))]
            if isinstance(item, dict)
        ]
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(self, path: str, params: dict | None = None) -> dict:
        """Issue GET to CrossRef API and return the ``message`` payload."""
        url = f"{CROSSREF_API}{path}"
        try:
            resp = requests.get(
                url, params=params, headers=self._headers, timeout=self._timeout
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            raise DataSourceError(
                self.SOURCE_NAME,
                f"HTTP {status} from {url}",
                original_error=exc,
            ) from exc
        except requests.RequestException as exc:
            raise DataSourceError(
                self.SOURCE_NAME,
                f"Network error calling {url}: {exc}",
                original_error=exc,
            ) from exc

        return resp.json().get("message", {})

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_authors(author_list: list[dict], limit: int = 0) -> list[str]:
        """Convert CrossRef author entries to ``["Given Family", ...]`` list.

        Args:
            author_list: Raw ``author`` array from CrossRef.
            limit: Max authors to include; 0 = all.
        """
        subset = author_list[:limit] if limit else author_list
        names = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in subset
        ]
        if limit and len(author_list) > limit:
            names.append("et al.")
        return names

    @staticmethod
    def _extract_year(item: dict) -> int | None:
        """Best-effort publication year extraction."""
        for key in ("published-print", "published-online", "created"):
            parts = item.get(key, {}).get("date-parts", [[None]])
            year = parts[0][0] if parts and parts[0] else None
            if year is not None:
                return year
        return None

    def _normalize_search_item(self, item: dict) -> dict:
        """Map a CrossRef work item to the unified search result format."""
        return {
            "title": (item.get("title") or [""])[0],
            "authors": self._extract_authors(item.get("author", []), limit=5),
            "year": self._extract_year(item),
            "doi": item.get("DOI"),
            "journal": (item.get("container-title") or [""])[0],
            "language": item.get("language") or "",
            "document_type": item.get("type") or "",
            "source": self.SOURCE_NAME,
            "citation_count": item.get("is-referenced-by-count", 0),
        }

    def _normalize_detail_item(self, item: dict) -> dict:
        """Map a CrossRef work item to the unified detail result format."""
        base = self._normalize_search_item(item)
        base.update({
            "authors": self._extract_authors(item.get("author", [])),
            "abstract": item.get("abstract", ""),
            "volume": item.get("volume", ""),
            "issue": item.get("issue", ""),
            "pages": item.get("page", ""),
            "publisher": item.get("publisher", ""),
            "type": item.get("type"),
            "references_count": item.get("references-count", 0),
            "url": item.get("URL"),
        })
        return base


def _normalize_doi(value: str) -> str:
    normalized = str(value or "").strip().lower()
    normalized = normalized.removeprefix("doi:").strip()
    if normalized.startswith(("https://doi.org/", "http://doi.org/")):
        normalized = normalized.split("doi.org/", 1)[1]
    return normalized.rstrip(". ")


def _normalize_reference(item: dict) -> dict:
    doi = _normalize_doi(str(item.get("DOI") or item.get("doi") or ""))
    title = item.get("article-title") or item.get("article_title") or item.get("unstructured") or ""
    authors = []
    author = item.get("author")
    if author:
        authors = [str(author).strip()]
    year = item.get("year")
    try:
        year = int(year) if year not in (None, "") else None
    except (TypeError, ValueError):
        year = None
    source_url = f"https://doi.org/{doi}" if doi else ""
    source_id = doi or str(title).strip()
    return {
        "entity_type": "publication",
        "title": str(title).strip(),
        "authors": authors,
        "year": year,
        "journal": str(item.get("journal-title") or item.get("journal_title") or ""),
        "doi": doi,
            "source": CrossRefSource.SOURCE_NAME,
        "source_id": source_id,
        "source_url": source_url,
        "source_records": [
            {
                "source": CrossRefSource.SOURCE_NAME,
                "source_id": source_id,
                "source_url": source_url,
            }
        ],
    }
