"""Deterministic local relevance ranking for scholarly records."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SCORE_VERSION = "1"


def rank_records(
    records: Sequence[Mapping[str, Any]], query: str, *, mode: str = "relevance"
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if mode not in {"relevance", "none"}:
        raise ValueError("ranking must be 'relevance' or 'none'")
    copied = [dict(record) for record in records]
    if mode == "none":
        return copied, {"mode": "none", "score_version": "none"}

    query_text = query.strip().casefold()
    terms = _tokens(query_text)
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    for record in copied:
        score, reasons = _score_record(record, query_text, terms)
        record["ranking_score"] = score
        record["ranking_reasons"] = reasons
        ranked.append((score, str(record.get("record_id") or ""), record))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [record for _, _, record in ranked], {
        "mode": "relevance",
        "score_version": SCORE_VERSION,
    }


def _score_record(
    record: Mapping[str, Any], query: str, terms: list[str]
) -> tuple[float, list[str]]:
    title = str(record.get("title") or "").casefold()
    abstract = str(record.get("abstract") or "").casefold()
    subjects = " ".join(
        str(record.get(field) or "")
        for field in ("keywords", "subjects", "categories", "mesh_terms")
    ).casefold()
    score = 0.0
    reasons: list[str] = []
    for term in terms:
        if term in title:
            score += 5.0
            reasons.append(f"title:{term}")
        elif term in abstract:
            score += 2.0
            reasons.append(f"abstract:{term}")
        elif term in subjects:
            score += 1.0
            reasons.append(f"subject:{term}")

    if query and query in title:
        score += 3.0
        reasons.append("title:exact phrase")
    if _identifier_matches(record, query):
        score += 100.0
        reasons.append("identifier:exact match")
    return score, reasons


def _tokens(value: str) -> list[str]:
    tokens = [token for token in re.split(r"[^\w]+", value, flags=re.UNICODE) if token]
    return list(dict.fromkeys(tokens))


def _identifier_matches(record: Mapping[str, Any], query: str) -> bool:
    normalized = query.strip().casefold()
    if not normalized:
        return False
    fields = ("doi", "pmid", "pmcid", "arxiv_id", "openalex_id", "semantic_scholar_id", "nct_id")
    if any(str(record.get(field) or "").strip().casefold() == normalized for field in fields):
        return True
    record_id = str(record.get("record_id") or "").casefold()
    return record_id.rsplit(":", 1)[-1] == normalized
