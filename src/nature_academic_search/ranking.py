"""Deterministic local relevance ranking for scholarly records."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SCORE_VERSION = "2"
CJK_CHAR = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
CJK_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")
LATIN_TOKEN = re.compile(r"[a-z][a-z0-9_+-]*|\d+(?:\.\d+)+", flags=re.IGNORECASE)


def analyze_query(query: str) -> dict[str, Any]:
    """Split a mixed Chinese/English query into ranking terms and agent hints."""
    text = query.strip()
    latin_terms = [token.casefold() for token in LATIN_TOKEN.findall(text)]
    cjk_terms: list[str] = []
    for run in CJK_RUN.findall(text):
        if len(run) == 1:
            cjk_terms.append(run)
            continue
        cjk_terms.extend(run[index : index + 2] for index in range(len(run) - 1))
    contains_cjk = bool(cjk_terms)
    return {
        "contains_cjk": contains_cjk,
        "latin_terms": list(dict.fromkeys(latin_terms)),
        "cjk_terms": list(dict.fromkeys(cjk_terms)),
        "mesh_required": contains_cjk,
    }


def rank_records(
    records: Sequence[Mapping[str, Any]], query: str, *, mode: str = "relevance"
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if mode not in {"relevance", "none"}:
        raise ValueError("ranking must be 'relevance' or 'none'")
    copied = [dict(record) for record in records]
    if mode == "none":
        return copied, {"mode": "none", "score_version": "none"}

    query_text = query.strip().casefold()
    terms = _tokens(query)
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
    analysis = analyze_query(value)
    remainder = CJK_CHAR.sub(" ", value)
    latin_words = [
        token.casefold()
        for token in re.split(r"[^\w]+", remainder, flags=re.UNICODE)
        if token and not CJK_CHAR.search(token)
    ]
    return list(
        dict.fromkeys([*latin_words, *analysis["latin_terms"], *analysis["cjk_terms"]])
    )


def _identifier_matches(record: Mapping[str, Any], query: str) -> bool:
    normalized = query.strip().casefold()
    if not normalized:
        return False
    fields = ("doi", "pmid", "pmcid", "arxiv_id", "openalex_id", "semantic_scholar_id", "nct_id")
    if any(str(record.get(field) or "").strip().casefold() == normalized for field in fields):
        return True
    record_id = str(record.get("record_id") or "").casefold()
    return record_id.rsplit(":", 1)[-1] == normalized
