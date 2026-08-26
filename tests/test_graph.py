from __future__ import annotations

import pytest

from nature_academic_search.graph import build_citation_graph

SEED = {
    "entity_type": "publication",
    "record_id": "publication:doi:10.1000/seed",
    "doi": "10.1000/seed",
    "title": "Seed paper",
    "year": 2024,
}


class FakeRelationSource:
    def __init__(self, payload=None, error: Exception | None = None):
        self.payload = payload or {}
        self.error = error
        self.calls: list[tuple[str, str, int]] = []

    def get_citation_relations(self, identifier: str, relation: str, rows: int) -> dict:
        self.calls.append((identifier, relation, rows))
        if self.error:
            raise self.error
        return self.payload


def record(record_id: str, title: str) -> dict:
    return {
        "entity_type": "publication",
        "record_id": record_id,
        "doi": record_id.rsplit(":", 1)[-1],
        "title": title,
        "year": 2024,
    }


def test_build_citation_graph_merges_cross_source_edges_and_preserves_direction() -> None:
    cited = record("publication:doi:10.1000/cited", "Cited paper")
    citing = record("publication:doi:10.1000/citing", "Citing paper")
    adapters = {
        "openalex": FakeRelationSource(
            {
                "references": [cited],
                "cited_by": [citing],
            }
        ),
        "crossref": FakeRelationSource(
            {"references": [cited], "cited_by": []}
        ),
    }

    graph = build_citation_graph(
        SEED,
        relation="both",
        depth=1,
        rows=10,
        relation_sources=["openalex", "crossref"],
        adapters=adapters,
    )

    assert graph["schema_version"] == "1"
    assert graph["seed_record_id"] == SEED["record_id"]
    assert graph["direction"] == "both"
    assert graph["depth_completed"] == 1
    assert [node["record_id"] for node in graph["nodes"]] == [
        SEED["record_id"],
        cited["record_id"],
        citing["record_id"],
    ]
    assert graph["edges"] == [
        {
            "from": citing["record_id"],
            "to": SEED["record_id"],
            "relation": "cited_by",
            "observed_by": ["openalex"],
        },
        {
            "from": SEED["record_id"],
            "to": cited["record_id"],
            "relation": "references",
            "observed_by": ["crossref", "openalex"],
        },
    ]
    assert graph["sources_queried"] == ["openalex", "crossref"]
    assert graph["sources_succeeded"] == ["openalex", "crossref"]
    assert graph["errors"] is None


def test_build_citation_graph_depth_two_is_bounded_and_deterministic() -> None:
    second = record("publication:doi:10.1000/second", "Second")
    third = record("publication:doi:10.1000/third", "Third")
    adapters = {
        "openalex": FakeRelationSource(
            {"references": [second, third], "cited_by": []}
        )
    }

    graph = build_citation_graph(
        SEED,
        relation="references",
        depth=2,
        rows=10,
        max_nodes=2,
        relation_sources=["openalex"],
        adapters=adapters,
    )

    assert graph["depth_requested"] == 2
    assert graph["depth_completed"] == 1
    assert graph["truncated"] is True
    assert graph["truncation_reason"] == "max_nodes"
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1


def test_build_citation_graph_keeps_successful_sources_when_one_fails() -> None:
    cited = record("publication:doi:10.1000/cited", "Cited")
    adapters = {
        "openalex": FakeRelationSource({"references": [cited], "cited_by": []}),
        "semantic_scholar": FakeRelationSource(error=RuntimeError("HTTP 429")),
    }

    graph = build_citation_graph(
        SEED,
        relation="references",
        relation_sources=["openalex", "semantic_scholar"],
        adapters=adapters,
    )

    assert len(graph["edges"]) == 1
    assert graph["sources_succeeded"] == ["openalex"]
    assert graph["errors"][0]["source"] == "semantic_scholar"
    assert graph["errors"][0]["error"] == "HTTP 429"


def test_build_citation_graph_validates_bounds_and_direction() -> None:
    with pytest.raises(ValueError, match="relation"):
        build_citation_graph(SEED, relation="unknown")
    with pytest.raises(ValueError, match="depth"):
        build_citation_graph(SEED, depth=3)
    with pytest.raises(ValueError, match="rows"):
        build_citation_graph(SEED, rows=0)


def test_build_citation_graph_does_not_leave_dangling_node_at_edge_limit() -> None:
    first = record("publication:doi:10.1000/first", "First")
    second = record("publication:doi:10.1000/second", "Second")
    graph = build_citation_graph(
        SEED,
        relation="references",
        relation_sources=["openalex"],
        adapters={"openalex": FakeRelationSource({"references": [first, second]})},
        max_edges=1,
    )

    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
    assert graph["truncation_reason"] == "max_edges"
