# Multi-Source Citation Graph Design

## Goal

Add a source-aware citation neighborhood to the existing academic search skill so users can inspect both
the papers a work references and the works that cite it, with optional multi-hop expansion and auditable
partial results.

## Scope

The first release extends `get_paper_by_id` with optional `include_relations`, `relation`, `depth`, `rows`,
and `relation_sources` parameters. Existing calls and the four MCP tool names remain unchanged. The default
is no graph lookup; when enabled, depth 1 is used unless explicitly set to 2.

## Source-Aware Strategy

- OpenAlex is the cross-disciplinary primary source: `referenced_works` provides outgoing edges and `cites`
  filtering provides incoming edges.
- Crossref contributes DOI work reference lists.
- PubMed ELink contributes biomedical `refs` and `citedin` links.
- Europe PMC contributes biomedical reference records where available.
- Semantic Scholar contributes optional `references` and `citations` edges.
- arXiv remains a node/identifier source; its API is not treated as a citation-edge source.

The runner never interprets a missing edge from one source as proof that no relationship exists. Source
coverage, skips, errors, truncation, and retrieval timestamps are included in the graph artifact.

## Graph Contract

```json
{
  "schema_version": "1",
  "seed_record_id": "publication:doi:10.x/example",
  "direction": "both",
  "depth_requested": 1,
  "depth_completed": 1,
  "nodes": [],
  "edges": [],
  "sources_queried": [],
  "sources_succeeded": [],
  "sources_skipped": [],
  "errors": null,
  "truncated": false,
  "coverage_notes": []
}
```

Nodes reuse the existing normalized publication record and `record_id`. Edges contain `from`, `to`,
`relation` (`references` or `cited_by`), `observed_by`, and source records. Identical edges observed by
multiple sources are merged rather than counted repeatedly.

## Safety and Reproducibility

- BFS traversal is deterministic; `record_id` breaks ties.
- `depth=2` is explicit and bounded by `max_nodes`, `max_edges`, and per-source `rows`.
- Each source is isolated for timeout, rate limit, malformed data, and partial failure.
- No citation graph score is presented as evidence quality, impact, causality, or recommendation.
- Graph JSON is the source artifact; Mermaid/GraphML rendering is a follow-up presentation layer.
