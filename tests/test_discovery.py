from __future__ import annotations

import pytest

from nature_academic_search.discovery import (
    analyze_query,
    apply_post_filters,
    normalize_filters,
    rank_records,
    translate_filters,
)


def test_normalize_filters_validates_dates_and_keeps_document_type() -> None:
    filters = normalize_filters(
        {
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "language": "EN",
            "author": "Jane Doe",
            "document_type": "journal-article",
            "identifiers": ["10.1000/ABC"],
        }
    )

    assert filters == {
        "date_from": "2024-01-01",
        "date_to": "2024-12-31",
        "language": "en",
        "author": "Jane Doe",
        "document_type": ["journal-article"],
        "identifiers": ["10.1000/abc"],
    }


def test_normalize_filters_rejects_unknown_fields_and_reversed_dates() -> None:
    with pytest.raises(ValueError, match="Unknown filter"):
        normalize_filters({"not_a_filter": "x"})
    with pytest.raises(ValueError, match="date_from"):
        normalize_filters({"date_from": "2025-01-01", "date_to": "2024-01-01"})


def test_translate_filters_exposes_supported_and_deferred_fields() -> None:
    filters = normalize_filters(
        {
            "date_from": "2024-01-01",
            "language": "en",
            "author": "Jane Doe",
            "document_type": "journal-article",
        }
    )

    crossref = translate_filters("crossref", filters)
    assert crossref["kwargs"]["date_from"] == "2024-01-01"
    assert crossref["kwargs"]["author"] == "Jane Doe"
    assert "language" in crossref["post_filter"]
    assert "document_type" in crossref["applied"]

    pubmed = translate_filters("pubmed", filters)
    assert "2024/01/01" in pubmed["query"]
    assert "Jane Doe[Author]" in pubmed["query"]


def test_apply_post_filters_is_deterministic_and_keeps_partial_metadata() -> None:
    records = [
        {"title": "English study", "language": "en", "year": 2024},
        {"title": "French study", "language": "fr", "year": 2024},
        {"title": "Missing language", "year": 2024},
    ]

    filtered = apply_post_filters(records, normalize_filters({"language": "en"}))

    assert [record["title"] for record in filtered] == ["English study"]


def test_rank_records_returns_fixed_version_scores_reasons_and_tie_breaker() -> None:
    records = [
        {
            "record_id": "publication:doi:10.1/b",
            "title": "AI safety in medicine",
            "abstract": "A study of medicine",
        },
        {
            "record_id": "publication:doi:10.1/a",
            "title": "Medicine",
            "abstract": "AI safety in medicine",
        },
    ]

    ranked, metadata = rank_records(records, "AI safety", mode="relevance")

    assert metadata == {"mode": "relevance", "score_version": "2"}
    assert [record["record_id"] for record in ranked] == [
        "publication:doi:10.1/b",
        "publication:doi:10.1/a",
    ]
    assert ranked[0]["ranking_score"] > ranked[1]["ranking_score"]
    assert ranked[0]["ranking_reasons"]


def test_rank_records_exact_identifier_match_is_strong_signal() -> None:
    records = [
        {"record_id": "publication:doi:10.1000/example", "title": "Other"},
        {"record_id": "publication:doi:10.1000/target", "title": "Other"},
    ]

    ranked, _ = rank_records(records, "10.1000/target", mode="relevance")

    assert ranked[0]["record_id"] == "publication:doi:10.1000/target"
    assert any("identifier" in reason for reason in ranked[0]["ranking_reasons"])


def test_analyze_query_flags_chinese_and_keeps_latin_terms() -> None:
    analysis = analyze_query("生成式 AI 医学教育")

    assert analysis["contains_cjk"] is True
    assert analysis["mesh_required"] is True
    assert "ai" in analysis["latin_terms"]
    assert "医学" in analysis["cjk_terms"]
    assert "教育" in analysis["cjk_terms"]


def test_rank_records_uses_latin_terms_from_chinese_query() -> None:
    records = [
        {
            "record_id": "publication:doi:10.1/ai",
            "title": "Generative AI in medical education",
            "abstract": "A review",
        },
        {
            "record_id": "publication:doi:10.1/other",
            "title": "Unrelated chemistry",
            "abstract": "synthesis",
        },
    ]

    ranked, metadata = rank_records(records, "生成式 AI 医学教育", mode="relevance")

    assert metadata["score_version"] == "2"
    assert ranked[0]["record_id"] == "publication:doi:10.1/ai"
    assert any("ai" in reason for reason in ranked[0]["ranking_reasons"])


def test_rank_records_matches_chinese_bigrams_in_title() -> None:
    records = [
        {"record_id": "a", "title": "生成式人工智能与医学教育", "abstract": ""},
        {"record_id": "b", "title": "无关标题", "abstract": ""},
    ]

    ranked, _ = rank_records(records, "医学教育", mode="relevance")

    assert ranked[0]["record_id"] == "a"
    assert any("医学" in reason or "教育" in reason for reason in ranked[0]["ranking_reasons"])


def test_rank_records_none_preserves_input_without_scores() -> None:
    records = [{"record_id": "b"}, {"record_id": "a"}]

    ranked, metadata = rank_records(records, "query", mode="none")

    assert [record["record_id"] for record in ranked] == ["b", "a"]
    assert metadata == {"mode": "none", "score_version": "none"}
    assert "ranking_score" not in ranked[0]
