"""Multi-source search coordination and record deduplication."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .sources.registry import (
    DEFAULT_PUBLICATION_SOURCES,
    build_adapters,
    source_capabilities,
)

IDENTIFIER_FIELDS = (
    "doi",
    "pmid",
    "pmcid",
    "arxiv_id",
    "openalex_id",
    "semantic_scholar_id",
    "nct_id",
)


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
    sources: Sequence[str] | None,
    rows: int,
    *,
    filter_type: str | None = None,
    adapters: Mapping[str, Any] | None = None,
    enrichers: Sequence[str] | None = None,
) -> dict[str, Any]:
    selected_sources = list(sources or DEFAULT_PUBLICATION_SOURCES)
    selected_enrichers = list(enrichers or [])
    needed_sources = list(dict.fromkeys([*selected_sources, *selected_enrichers]))
    selected_adapters = dict(adapters or build_adapters(needed_sources))
    missing = [source for source in needed_sources if source not in selected_adapters]
    if missing:
        raise ValueError(f"Missing adapters for sources: {missing}")
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
        for source in selected_sources
    ]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    raw_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    succeeded: list[str] = []
    source_meta: dict[str, Any] = {}
    total = 0
    for source, outcome in zip(selected_sources, outcomes):
        if isinstance(outcome, BaseException):
            errors.append(_source_error(source, outcome))
            continue
        succeeded.append(source)
        total += int(outcome.get("total", 0))
        if outcome.get("source_meta"):
            source_meta[source] = outcome["source_meta"]
        for result in outcome.get("results", []):
            record = dict(result)
            record.setdefault("source", source)
            raw_records.append(record)

    results = deduplicate_records(raw_records)
    enrichment = await enrich_records(
        results,
        selected_enrichers,
        adapters=selected_adapters,
        limit=rows,
    )
    results = enrichment["results"]
    errors.extend(enrichment["errors"])
    return {
        "total": total,
        "sources_queried": selected_sources,
        "sources_succeeded": succeeded,
        "sources_skipped": enrichment["skipped"],
        "enrichment_sources": selected_enrichers,
        "source_meta": source_meta,
        "raw_result_count": len(raw_records),
        "result_count": len(results),
        "results": results,
        "errors": errors or None,
    }


async def enrich_records(
    records: Sequence[Mapping[str, Any]],
    enrichers: Sequence[str],
    *,
    adapters: Mapping[str, Any] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Enrich a bounded set of records using strong identifiers only."""
    results = [_prepare_record(record) for record in records]
    if not enrichers:
        return {"results": results, "errors": [], "skipped": []}

    selected_adapters = dict(adapters or build_adapters(list(enrichers)))
    errors: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    upper_bound = len(results) if limit is None else min(max(limit, 0), len(results))

    for source in enrichers:
        if "enrich" not in source_capabilities(source):
            raise ValueError(f"Source does not support enrichment: {source}")
        adapter = selected_adapters[source]
        for index, record in enumerate(results[:upper_bound]):
            identifier = _strong_identifier(record)
            if identifier is None:
                skipped.append(
                    {
                        "source": source,
                        "record_index": index,
                        "reason": "missing strong identifier",
                    }
                )
                continue
            try:
                incoming = await asyncio.to_thread(adapter.get_by_id, identifier)
            except Exception as exc:
                error = _source_error(source, exc)
                error["record_index"] = index
                errors.append(error)
                continue
            _merge_record(record, _prepare_record(incoming))

    return {"results": results, "errors": errors, "skipped": skipped}


def _search_one(
    source: str,
    adapter: Any,
    query: str,
    rows: int,
    filter_type: str | None,
) -> dict[str, Any]:
    if filter_type and "type_filter" in source_capabilities(source):
        return adapter.search(query, rows=rows, filter_type=filter_type)
    return adapter.search(query, rows=rows)


def _prepare_record(raw_record: Mapping[str, Any]) -> dict[str, Any]:
    record = dict(raw_record)
    record.setdefault("entity_type", "publication")
    if record.get("doi"):
        record["doi"] = _normalize_doi(str(record["doi"]))
    if record.get("pmid") is not None:
        record["pmid"] = str(record["pmid"]).strip()
    if record.get("arxiv_id"):
        record["arxiv_id"] = _normalize_arxiv_id(str(record["arxiv_id"]))
    if record.get("pmcid"):
        record["pmcid"] = str(record["pmcid"]).strip().upper()
    if record.get("openalex_id"):
        record["openalex_id"] = str(record["openalex_id"]).strip().upper()
    if record.get("semantic_scholar_id"):
        record["semantic_scholar_id"] = str(record["semantic_scholar_id"]).strip()
    if record.get("nct_id"):
        record["nct_id"] = str(record["nct_id"]).strip().upper()

    sources = list(record.get("sources") or [])
    if record.get("source") and record["source"] not in sources:
        sources.append(record["source"])
    record["sources"] = sources
    record["source_records"] = _source_records(record)
    record.setdefault("conflicts", [])

    source = str(record.get("citation_count_source") or record.get("source") or "")
    counts = dict(record.get("citation_counts") or {})
    if record.get("citation_count") is not None and source:
        counts.setdefault(source, int(record["citation_count"] or 0))
        record["citation_count_source"] = source
    record["citation_counts"] = counts
    return record


def _record_keys(record: Mapping[str, Any]) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    entity_type = str(record.get("entity_type") or "publication")
    identifier_fields = ("nct_id",) if entity_type == "trial" else IDENTIFIER_FIELDS[:-1]
    for field in identifier_fields:
        value = record.get(field)
        if value:
            keys.append((f"{entity_type}:{field}", str(value)))

    if entity_type == "publication":
        title = _normalize_title(str(record.get("title") or ""))
        year = record.get("year")
        if title and year not in (None, ""):
            keys.append((f"{entity_type}:title_year", f"{title}:{year}"))
    return keys


def _merge_record(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for source in incoming.get("sources") or []:
        if source not in target["sources"]:
            target["sources"].append(source)

    for source_record in incoming.get("source_records") or []:
        if source_record not in target["source_records"]:
            target["source_records"].append(source_record)

    target_counts = target.setdefault("citation_counts", {})
    target_counts.update(incoming.get("citation_counts") or {})
    incoming_source = str(
        incoming.get("citation_count_source") or incoming.get("source") or ""
    )
    incoming_count = incoming.get("citation_count") or 0
    if incoming.get("citation_count") is not None and incoming_source:
        target_counts[incoming_source] = int(incoming_count)

    target_count = target.get("citation_count") or 0
    if incoming_count > target_count:
        target["citation_count"] = incoming_count
        target["citation_count_source"] = incoming_source

    for field in IDENTIFIER_FIELDS:
        kept = target.get(field)
        value = incoming.get(field)
        if kept not in (None, "") and value not in (None, "") and kept != value:
            conflict = {
                "field": field,
                "kept": kept,
                "incoming": value,
                "source": incoming.get("source"),
            }
            if conflict not in target["conflicts"]:
                target["conflicts"].append(conflict)

    for key, value in incoming.items():
        if key in {
            "source",
            "sources",
            "source_records",
            "citation_count",
            "citation_count_source",
            "citation_counts",
            "conflicts",
        }:
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


def _source_records(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = [
        dict(item)
        for item in record.get("source_records") or []
        if isinstance(item, Mapping)
    ]
    source = record.get("source")
    source_id = record.get("source_id")
    source_url = record.get("source_url")
    if source and (source_id or source_url):
        current = {
            "source": source,
            "source_id": source_id or "",
            "source_url": source_url or "",
        }
        if current not in records:
            records.append(current)
    return records


def _source_error(source: str, error: BaseException) -> dict[str, Any]:
    message = str(error)
    status_match = re.search(r"HTTP (\d{3})", message)
    status = int(status_match.group(1)) if status_match else None
    retryable = status in {429, 502, 503, 504} or "timed out" in message.casefold()
    kind = "rate_limited" if status == 429 else "source_error"
    payload: dict[str, Any] = {
        "source": source,
        "error": message,
        "kind": kind,
        "retryable": retryable,
    }
    if status is not None:
        payload["status"] = status
    return payload


def _strong_identifier(record: Mapping[str, Any]) -> str | None:
    if record.get("doi"):
        return f"DOI:{record['doi']}"
    if record.get("arxiv_id"):
        return f"ARXIV:{record['arxiv_id']}"
    if record.get("pmid"):
        return f"PMID:{record['pmid']}"
    if record.get("semantic_scholar_id"):
        return str(record["semantic_scholar_id"])
    return None
