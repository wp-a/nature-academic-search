from __future__ import annotations

from nature_academic_search.provenance import result_fingerprint, stable_record_id


def test_strong_identifier_record_id_is_canonical() -> None:
    record = {"entity_type": "publication", "doi": "https://doi.org/10.1000/ABC."}

    assert stable_record_id(record) == "publication:doi:10.1000/abc"


def test_fallback_record_id_is_stable_across_mapping_order() -> None:
    first = {"title": "A Study", "year": 2024, "authors": ["Jane Doe"]}
    second = {"authors": ["Jane Doe"], "year": "2024", "title": "A study"}

    assert stable_record_id(first) == stable_record_id(second)


def test_trial_identifier_uses_trial_namespace() -> None:
    record = {"entity_type": "trial", "nct_id": "nct01234567"}

    assert stable_record_id(record) == "trial:nct:NCT01234567"


def test_fingerprint_depends_on_ordered_record_ids() -> None:
    first = result_fingerprint(["publication:doi:10.1/a"])
    second = result_fingerprint(["publication:doi:10.1/b"])

    assert first.startswith("sha256:")
    assert first != second
