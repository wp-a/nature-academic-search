from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from nature_academic_search.errors import DataSourceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sources" / "clinicaltrials-search.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def config() -> SimpleNamespace:
    return SimpleNamespace(clinicaltrials_gov_timeout=19, max_rows=50)


def test_search_normalizes_clinical_trial() -> None:
    from nature_academic_search.sources.clinicaltrials import ClinicalTrialsSource

    with (
        patch(
            "nature_academic_search.sources.clinicaltrials.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.clinicaltrials.request_json",
            return_value=(load_fixture(), {}),
        ) as request,
    ):
        result = ClinicalTrialsSource().search("example", rows=5)

    assert request.call_args.kwargs["url"].endswith("/api/v2/studies")
    assert request.call_args.kwargs["params"] == {
        "query.term": "example",
        "pageSize": 5,
        "format": "json",
        "countTotal": "true",
    }
    assert result["total"] == 1
    assert result["source"] == "clinicaltrials_gov"
    trial = result["results"][0]
    assert trial["entity_type"] == "trial"
    assert trial["nct_id"] == "NCT01234567"
    assert trial["source_id"] == "NCT01234567"
    assert trial["title"] == "A fictional example trial"
    assert trial["brief_title"] == "Example trial"
    assert trial["study_type"] == "INTERVENTIONAL"
    assert trial["overall_status"] == "RECRUITING"
    assert trial["conditions"] == ["Example condition"]
    assert trial["interventions"] == [
        {"type": "DRUG", "name": "Example intervention"}
    ]
    assert trial["sponsor"] == "Example University"
    assert trial["enrollment"] == 120
    assert trial["locations"] == [
        {
            "facility": "Example Hospital",
            "city": "Example City",
            "country": "Example Country",
        }
    ]
    assert trial["start_date"] == "2025-01"
    assert trial["completion_date"] == "2027-06"
    assert trial["last_update_posted"] == "2026-07-01"
    assert trial["registry_data_timestamp"] == "2026-07-20"
    assert trial["linked_publications"] == []
    assert "citation_count" not in trial


def test_search_caps_rows_and_handles_zero_results() -> None:
    from nature_academic_search.sources.clinicaltrials import ClinicalTrialsSource

    with (
        patch(
            "nature_academic_search.sources.clinicaltrials.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.clinicaltrials.request_json",
            return_value=({"totalCount": 0, "studies": []}, {}),
        ) as request,
    ):
        result = ClinicalTrialsSource().search("example", rows=500)

    assert result["results"] == []
    assert request.call_args.kwargs["params"]["pageSize"] == 50


@pytest.mark.parametrize(
    "identifier",
    [
        "NCT01234567",
        "https://clinicaltrials.gov/study/NCT01234567",
    ],
)
def test_get_by_id_normalizes_nct_identifier(identifier: str) -> None:
    from nature_academic_search.sources.clinicaltrials import ClinicalTrialsSource

    study = load_fixture()["studies"][0]
    with (
        patch(
            "nature_academic_search.sources.clinicaltrials.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.clinicaltrials.request_json",
            return_value=(study, {}),
        ) as request,
    ):
        trial = ClinicalTrialsSource().get_by_id(identifier)

    assert request.call_args.kwargs["url"].endswith("/studies/NCT01234567")
    assert trial["nct_id"] == "NCT01234567"


def test_search_rejects_empty_query_and_malformed_payload() -> None:
    from nature_academic_search.sources.clinicaltrials import ClinicalTrialsSource

    with pytest.raises(DataSourceError, match="Empty search query"):
        ClinicalTrialsSource().search(" ")

    with (
        patch(
            "nature_academic_search.sources.clinicaltrials.get_config",
            return_value=config(),
        ),
        patch(
            "nature_academic_search.sources.clinicaltrials.request_json",
            return_value=({"totalCount": 1, "studies": {}}, {}),
        ),
        pytest.raises(DataSourceError, match="Malformed search response"),
    ):
        ClinicalTrialsSource().search("example")
