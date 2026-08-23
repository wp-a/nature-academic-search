from __future__ import annotations

from nature_academic_search.verification import verify_record


def test_matching_title_author_year_and_doi_is_verified() -> None:
    actual = {
        "entity_type": "publication",
        "title": "A Study of Retrieval",
        "authors": ["Jane Doe", "John Smith"],
        "year": 2024,
        "journal": "Journal of Tests",
        "doi": "10.1000/example",
    }

    result = verify_record(
        {
            "title": "A Study of Retrieval",
            "authors": ["Jane Doe"],
            "year": "2024",
            "doi": "https://doi.org/10.1000/EXAMPLE",
        },
        actual,
    )

    assert result["status"] == "verified"
    assert result["method"] == "identifier_lookup"
    assert all(field["status"] == "match" for field in result["fields"].values())


def test_conflicting_year_reports_mismatch_without_overwriting_actual() -> None:
    actual = {
        "entity_type": "publication",
        "title": "A Study",
        "year": 2023,
        "doi": "10.1000/example",
    }

    result = verify_record({"title": "A Study", "year": 2024}, actual)

    assert result["status"] == "mismatch"
    assert result["fields"]["year"] == {
        "status": "mismatch",
        "expected": 2024,
        "actual": 2023,
    }
    assert actual["year"] == 2023


def test_missing_expected_metadata_is_manual_needed() -> None:
    result = verify_record({}, {"entity_type": "publication", "title": "A Study"})

    assert result == {
        "status": "manual_needed",
        "fields": {},
        "method": "identifier_lookup",
    }


def test_missing_actual_field_is_manual_needed() -> None:
    result = verify_record(
        {"title": "A Study", "journal": "Journal of Tests"},
        {"entity_type": "publication", "title": "A Study"},
    )

    assert result["status"] == "manual_needed"
    assert result["fields"]["journal"]["status"] == "missing"


def test_missing_record_is_not_found() -> None:
    result = verify_record({"doi": "10.1000/missing"}, None)

    assert result == {
        "status": "not_found",
        "fields": {},
        "method": "identifier_lookup",
    }


def test_trial_expected_fields_use_nct_status_not_paper_journal() -> None:
    actual = {
        "entity_type": "trial",
        "nct_id": "NCT01234567",
        "title": "A Trial",
        "overall_status": "RECRUITING",
        "sponsor": "Example University",
    }

    result = verify_record(
        {
            "nct_id": "nct01234567",
            "title": "A Trial",
            "status": "recruiting",
            "sponsor": "Example University",
        },
        actual,
    )

    assert result["status"] == "verified"
    assert "journal" not in result["fields"]
