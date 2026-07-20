from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "sources"


def test_source_sets_are_entity_specific() -> None:
    from nature_academic_search.sources.registry import (
        DEFAULT_PUBLICATION_SOURCES,
        OPTIONAL_PUBLICATION_SOURCES,
        SOURCE_ENTITY_TYPES,
        TRIAL_SOURCES,
    )

    assert DEFAULT_PUBLICATION_SOURCES == (
        "crossref",
        "pubmed",
        "arxiv",
        "openalex",
        "europe_pmc",
    )
    assert OPTIONAL_PUBLICATION_SOURCES == ("semantic_scholar",)
    assert TRIAL_SOURCES == ("clinicaltrials_gov",)
    assert SOURCE_ENTITY_TYPES["openalex"] == "publication"
    assert SOURCE_ENTITY_TYPES["clinicaltrials_gov"] == "trial"


def test_source_fixtures_are_minimal_and_fictional() -> None:
    fixtures = sorted(FIXTURES.glob("*.json"))

    assert [path.name for path in fixtures] == [
        "clinicaltrials-search.json",
        "europe-pmc-search.json",
        "openalex-search.json",
        "semantic-scholar-search.json",
    ]
    for path in fixtures:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data
        assert "Example" in path.read_text(encoding="utf-8")
        assert path.stat().st_size < 5_000
