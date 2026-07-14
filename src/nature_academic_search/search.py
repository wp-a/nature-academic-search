"""Multi-source search coordination and record deduplication."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping, Sequence
from typing import Any


def deduplicate_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any] | None] = []
    key_to_group: dict[tuple[str, str], int] = {}

    for raw_record in records:
        record = _prepare_record(raw_record)
        keys = _record_keys(record)
        matches = sorted({key_to_group[key] for key in keys if key in key_to_group})

        if not matches:
            target = len(groups)
            groups.append(record)
        else:
            target = matches[0]
            for duplicate_group in matches[1:]:
                duplicate = groups[duplicate_group]
                if duplicate is not None:
                    _merge_record(groups[target], duplicate)  # type: ignore[arg-type]
                    groups[duplicate_group] = None
                    for key, group_index in tuple(key_to_group.items()):
                        if group_index == duplicate_group:
                            key_to_group[key] = target
            _merge_record(groups[target], record)  # type: ignore[arg-type]

        current = groups[target]
        if current is not None:
            for key in _record_keys(current):
                key_to_group[key] = target

    return [record for record in groups if record is not None]


async def search_all(
    query: str,
    sources: Sequence[str],
    rows: int,
    *,
    filter_type: str | None = None,
    adapters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected_adapters = dict(adapters or _default_adapters())
    tasks = [
        asyncio.create_task(
            asyncio.to_thread(
                _search_one,
                source,
                selected_adapters[source],
                query,
                rows,
                filter_type,
            )
        )
        for source in sources
    ]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    raw_records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    total = 0
    for source, outcome in zip(sources, outcomes):
        if isinstance(outcome, BaseException):
            errors.append({"source": source, "error": str(outcome)})
            continue
        total += int(outcome.get("total", 0))
        for result in outcome.get("results", []):
            record = dict(result)
            record.setdefault("source", source)
            raw_records.append(record)

    results = deduplicate_records(raw_records)
    return {
        "total": total,
        "sources_queried": list(sources),
        "raw_result_count": len(raw_records),
        "result_count": len(results),
        "results": results,
        "errors": errors or None,
    }


def _default_adapters() -> dict[str, Any]:
    from .sources import ArxivSource, CrossRefSource, PubMedSource

    return {
        "crossref": CrossRefSource(),
        "pubmed": PubMedSource(),
        "arxiv": ArxivSource(),
    }


def _search_one(
    source: str,
    adapter: Any,
    query: str,
    rows: int,
    filter_type: str | None,
) -> dict[str, Any]:
    if source == "crossref":
        return adapter.search(query, rows=rows, filter_type=filter_type)
    return adapter.search(query, rows=rows)


def _prepare_record(raw_record: Mapping[str, Any]) -> dict[str, Any]:
    record = dict(raw_record)
    if record.get("doi"):
        record["doi"] = _normalize_doi(str(record["doi"]))
    if record.get("pmid") is not None:
        record["pmid"] = str(record["pmid"]).strip()
    if record.get("arxiv_id"):
        record["arxiv_id"] = _normalize_arxiv_id(str(record["arxiv_id"]))

    sources = list(record.get("sources") or [])
    if record.get("source") and record["source"] not in sources:
        sources.append(record["source"])
    record["sources"] = sources
    return record


def _record_keys(record: Mapping[str, Any]) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for field in ("doi", "pmid", "arxiv_id"):
        value = record.get(field)
        if value:
            keys.append((field, str(value)))

    title = _normalize_title(str(record.get("title") or ""))
    year = record.get("year")
    if title and year not in (None, ""):
        keys.append(("title_year", f"{title}:{year}"))
    return keys


def _merge_record(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for source in incoming.get("sources") or []:
        if source not in target["sources"]:
            target["sources"].append(source)

    target_count = target.get("citation_count") or 0
    incoming_count = incoming.get("citation_count") or 0
    if incoming_count > target_count:
        target["citation_count"] = incoming_count

    for key, value in incoming.items():
        if key in {"source", "sources", "citation_count"}:
            continue
        if value not in (None, "", [], {}) and target.get(key) in (None, "", [], {}):
            target[key] = value


def _normalize_doi(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", "", normalized)
    return normalized.rstrip(". ")


def _normalize_arxiv_id(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", normalized)
    normalized = normalized.removesuffix(".pdf")
    return re.sub(r"v\d+$", "", normalized)


def _normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
