"""ClinicalTrials.gov API v2 adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..config import get_config
from ..errors import DataSourceError
from ..http import request_json

SOURCE_NAME = "clinicaltrials_gov"
BASE_URL = "https://clinicaltrials.gov/api/v2"


class ClinicalTrialsSource:
    """Search and resolve ClinicalTrials.gov registrations."""

    name = SOURCE_NAME

    def search(self, query: str, rows: int = 5) -> dict[str, Any]:
        if not query or not query.strip():
            raise DataSourceError(SOURCE_NAME, "Empty search query")
        config = get_config()
        payload, response_meta = request_json(
            source=SOURCE_NAME,
            method="GET",
            url=f"{BASE_URL}/studies",
            params={
                "query.term": query.strip(),
                "pageSize": max(1, min(rows, config.max_rows, 1_000)),
                "format": "json",
                "countTotal": "true",
            },
            timeout=config.clinicaltrials_gov_timeout,
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("studies"), list):
            raise DataSourceError(SOURCE_NAME, "Malformed search response")
        return {
            "total": int(payload.get("totalCount") or 0),
            "query": query,
            "source": SOURCE_NAME,
            "source_meta": {"rate_limit": response_meta} if response_meta else {},
            "results": [
                _normalize_study(study)
                for study in payload["studies"]
                if isinstance(study, dict)
            ],
        }

    def get_by_id(self, identifier: str) -> dict[str, Any]:
        nct_id = _normalize_nct_id(identifier)
        config = get_config()
        payload, _ = request_json(
            source=SOURCE_NAME,
            method="GET",
            url=f"{BASE_URL}/studies/{nct_id}",
            params={"format": "json"},
            timeout=config.clinicaltrials_gov_timeout,
        )
        if not isinstance(payload, dict):
            raise DataSourceError(SOURCE_NAME, "Malformed study response")
        return _normalize_study(payload)


def _normalize_study(study: dict[str, Any]) -> dict[str, Any]:
    protocol = _mapping(study.get("protocolSection"))
    identification = _mapping(protocol.get("identificationModule"))
    status = _mapping(protocol.get("statusModule"))
    design = _mapping(protocol.get("designModule"))
    conditions_module = _mapping(protocol.get("conditionsModule"))
    interventions_module = _mapping(protocol.get("armsInterventionsModule"))
    sponsors_module = _mapping(protocol.get("sponsorCollaboratorsModule"))
    locations_module = _mapping(protocol.get("contactsLocationsModule"))
    derived = _mapping(study.get("derivedSection"))
    misc = _mapping(derived.get("miscInfoModule"))

    nct_id = _normalize_nct_id(str(identification.get("nctId") or ""))
    source_url = f"https://clinicaltrials.gov/study/{nct_id}"
    enrollment = _mapping(design.get("enrollmentInfo"))
    lead_sponsor = _mapping(sponsors_module.get("leadSponsor"))
    interventions = [
        {
            "type": item.get("type"),
            "name": item.get("name"),
        }
        for item in interventions_module.get("interventions") or []
        if isinstance(item, dict) and (item.get("type") or item.get("name"))
    ]
    locations = [
        {
            key: item.get(key)
            for key in ("facility", "city", "state", "country")
            if item.get(key) not in (None, "")
        }
        for item in locations_module.get("locations") or []
        if isinstance(item, dict)
    ]

    return {
        "entity_type": "trial",
        "title": str(
            identification.get("officialTitle")
            or identification.get("briefTitle")
            or ""
        ),
        "brief_title": str(identification.get("briefTitle") or ""),
        "nct_id": nct_id,
        "study_type": design.get("studyType"),
        "overall_status": status.get("overallStatus"),
        "conditions": list(conditions_module.get("conditions") or []),
        "interventions": interventions,
        "sponsor": str(lead_sponsor.get("name") or ""),
        "enrollment": enrollment.get("count"),
        "enrollment_type": enrollment.get("type"),
        "locations": locations,
        "start_date": _date(status.get("startDateStruct")),
        "completion_date": _date(status.get("completionDateStruct")),
        "last_update_posted": _date(status.get("lastUpdatePostDateStruct")),
        "registry_data_timestamp": misc.get("versionHolder"),
        "linked_publications": _linked_publications(derived),
        "source": SOURCE_NAME,
        "source_id": nct_id,
        "source_url": source_url,
        "source_records": [
            {
                "source": SOURCE_NAME,
                "source_id": nct_id,
                "source_url": source_url,
            }
        ],
        "retrieved_at": _utc_now(),
    }


def _normalize_nct_id(value: str) -> str:
    match = re.search(r"NCT\d{8}", value, flags=re.IGNORECASE)
    if not match:
        raise DataSourceError(SOURCE_NAME, f"Invalid NCT identifier: {value}")
    return match.group(0).upper()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _date(value: Any) -> str | None:
    return _mapping(value).get("date")


def _linked_publications(derived: dict[str, Any]) -> list[dict[str, Any]]:
    references = _mapping(derived.get("referencesModule")).get("references") or []
    return [
        {
            key: item.get(key)
            for key in ("pmid", "type", "citation")
            if item.get(key) not in (None, "")
        }
        for item in references
        if isinstance(item, dict)
    ]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
