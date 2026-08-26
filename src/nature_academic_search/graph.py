"""Source-aware, bounded citation graph coordination."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .provenance import stable_record_id

DEFAULT_RELATION_SOURCES = (
    "openalex",
    "crossref",
    "pubmed",
    "europe_pmc",
    "semantic_scholar",
)
RELATIONS = frozenset({"references", "cited_by", "both"})


def build_citation_graph(
    seed: Mapping[str, Any],
    *,
    relation: str = "both",
    depth: int = 1,
    rows: int = 20,
    relation_sources: Sequence[str] | None = None,
    max_nodes: int = 100,
    max_edges: int = 200,
    adapters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic citation neighborhood without hiding source gaps."""
    _validate_options(relation, depth, rows, max_nodes, max_edges)
    if str(seed.get("entity_type") or "publication") != "publication":
        raise ValueError("Citation graphs support publication records only")

    selected_sources = list(
        dict.fromkeys(relation_sources or DEFAULT_RELATION_SOURCES)
    )
    selected_adapters = dict(adapters or {})
    seed_node = _node(seed)
    seed_id = str(seed_node["record_id"])
    nodes: dict[str, dict[str, Any]] = {seed_id: seed_node}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    queried: list[str] = []
    succeeded: list[str] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, Any]] = []
    frontier = [seed_node]
    truncated = False
    truncation_reason: str | None = None
    depth_completed = 0

    for current_depth in range(1, depth + 1):
        next_frontier: dict[str, dict[str, Any]] = {}
        for current in sorted(frontier, key=lambda item: str(item["record_id"])):
            current_id = str(current["record_id"])
            for source in selected_sources:
                adapter = selected_adapters.get(source)
                if adapter is None or not hasattr(adapter, "get_citation_relations"):
                    _append_skip(
                        skipped,
                        source,
                        "citation_edges_not_supported"
                        if adapter is not None
                        else "adapter_not_available",
                    )
                    continue
                requested_relations = _requested_relations(relation)
                capabilities = getattr(adapter, "RELATION_CAPABILITIES", None)
                if capabilities is not None:
                    supported_relations = tuple(
                        edge_relation
                        for edge_relation in requested_relations
                        if edge_relation in capabilities
                    )
                    if not supported_relations:
                        _append_skip(skipped, source, "relation_not_supported")
                        continue
                    adapter_relation = (
                        "both" if len(supported_relations) == 2 else supported_relations[0]
                    )
                else:
                    supported_relations = requested_relations
                    adapter_relation = relation
                identifier = _identifier_for_source(current, source)
                if not identifier:
                    _append_skip(skipped, source, "missing_source_identifier")
                    continue
                if source not in queried:
                    queried.append(source)
                try:
                    payload = adapter.get_citation_relations(
                        identifier,
                        adapter_relation,
                        rows,
                    )
                except Exception as exc:
                    errors.append(
                        {
                            "source": source,
                            "record_id": current_id,
                            "error": str(exc),
                        }
                    )
                    continue
                if source not in succeeded:
                    succeeded.append(source)

                for edge_relation in supported_relations:
                    related_records = payload.get(edge_relation, [])
                    if not isinstance(related_records, Sequence) or isinstance(
                        related_records, (str, bytes)
                    ):
                        errors.append(
                            {
                                "source": source,
                                "record_id": current_id,
                                "error": f"Malformed {edge_relation} relation payload",
                            }
                        )
                        continue
                    for raw_related in related_records:
                        if not isinstance(raw_related, Mapping):
                            continue
                        related = _node(raw_related)
                        related_id = str(related["record_id"])
                        if related_id == current_id:
                            continue
                        edge_from, edge_to = (
                            (current_id, related_id)
                            if edge_relation == "references"
                            else (related_id, current_id)
                        )
                        edge_key = (edge_from, edge_to, edge_relation)
                        if edge_key not in edges and len(edges) >= max_edges:
                            truncated = True
                            truncation_reason = "max_edges"
                            break
                        if related_id not in nodes:
                            if len(nodes) >= max_nodes:
                                truncated = True
                                truncation_reason = "max_nodes"
                                break
                            nodes[related_id] = related
                            next_frontier[related_id] = related
                        else:
                            _merge_node(nodes[related_id], related)

                        if edge_key not in edges:
                            edges[edge_key] = {
                                "from": edge_from,
                                "to": edge_to,
                                "relation": edge_relation,
                                "observed_by": [source],
                            }
                        elif source not in edges[edge_key]["observed_by"]:
                            edges[edge_key]["observed_by"].append(source)
                    if truncated:
                        break
                if truncated:
                    break
            if truncated:
                break
        depth_completed = current_depth
        if truncated or not next_frontier:
            break
        frontier = list(next_frontier.values())

    ordered_edges = sorted(
        edges.values(),
        key=lambda item: (item["from"], item["to"], item["relation"]),
    )
    for edge in ordered_edges:
        edge["observed_by"] = sorted(edge["observed_by"])
    ordered_nodes = [nodes[seed_id]] + [
        nodes[node_id] for node_id in sorted(nodes) if node_id != seed_id
    ]
    result: dict[str, Any] = {
        "schema_version": "1",
        "seed_record_id": seed_id,
        "direction": relation,
        "depth_requested": depth,
        "depth_completed": depth_completed,
        "nodes": ordered_nodes,
        "edges": ordered_edges,
        "sources_queried": queried,
        "sources_succeeded": succeeded,
        "sources_skipped": skipped,
        "errors": errors or None,
        "truncated": truncated,
        "coverage_notes": [
            "Missing source edges are not evidence that no citation relation exists.",
            "Citation relations do not measure evidence quality or causality.",
        ],
    }
    if truncation_reason:
        result["truncation_reason"] = truncation_reason
    return result


def _validate_options(
    relation: str,
    depth: int,
    rows: int,
    max_nodes: int,
    max_edges: int,
) -> None:
    if relation not in RELATIONS:
        raise ValueError("relation must be 'references', 'cited_by', or 'both'")
    if depth not in {1, 2}:
        raise ValueError("depth must be 1 or 2")
    if rows < 1 or rows > 100:
        raise ValueError("rows must be between 1 and 100")
    if max_nodes < 2:
        raise ValueError("max_nodes must be at least 2")
    if max_edges < 1:
        raise ValueError("max_edges must be at least 1")


def _node(record: Mapping[str, Any]) -> dict[str, Any]:
    node = dict(record)
    node.setdefault("entity_type", "publication")
    node["record_id"] = stable_record_id(node)
    return node


def _merge_node(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for key, value in incoming.items():
        if value not in (None, "", [], {}) and target.get(key) in (None, "", [], {}):
            target[key] = value


def _identifier_for_source(record: Mapping[str, Any], source: str) -> str:
    if source == "openalex":
        return str(record.get("openalex_id") or record.get("doi") or "")
    if source == "crossref":
        return str(record.get("doi") or "")
    if source == "pubmed":
        return str(record.get("pmid") or "")
    if source == "europe_pmc":
        return str(record.get("pmid") or record.get("pmcid") or "")
    if source == "semantic_scholar":
        if record.get("semantic_scholar_id"):
            return str(record["semantic_scholar_id"])
        if record.get("doi"):
            return str(record["doi"])
        if record.get("arxiv_id"):
            return str(record["arxiv_id"])
        if record.get("pmid"):
            return f"PMID:{record['pmid']}"
    return ""


def _requested_relations(relation: str) -> tuple[str, ...]:
    return ("references", "cited_by") if relation == "both" else (relation,)


def _append_skip(skipped: list[dict[str, str]], source: str, reason: str) -> None:
    item = {"source": source, "reason": reason}
    if item not in skipped:
        skipped.append(item)
