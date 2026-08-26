# Multi-Source Citation Graph Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a multi-source, source-aware citation graph with one-hop default and explicit two-hop expansion.

**Architecture:** Add a graph coordinator that resolves the seed through existing adapters, queries source-specific relation endpoints, normalizes nodes and edges, and reports coverage/partial failures. Expose it as optional parameters on `get_paper_by_id` so old MCP calls remain unchanged.

**Tech Stack:** Python 3.10+, requests, asyncio, pytest, JSON, existing source adapters

---

### Task 1: Add failing graph contract tests

**Files:**
- Create: `tests/test_graph.py`
- Modify: `tests/test_server.py`

Cover direction validation, one-hop graph shape, cross-source edge merging, deterministic traversal,
truncation, source failure reporting, and backward-compatible calls without `include_relations`.

### Task 2: Implement normalized graph coordinator

**Files:**
- Create: `src/nature_academic_search/graph.py`

Implement `build_citation_graph` with bounded BFS, stable node IDs, edge normalization, source status,
and per-source relation dispatch. No source failure may discard successful edges.

### Task 3: Add source relation adapters

**Files:**
- Modify: `src/nature_academic_search/sources/openalex.py`
- Modify: `src/nature_academic_search/sources/crossref.py`
- Modify: `src/nature_academic_search/sources/pubmed.py`
- Modify: `src/nature_academic_search/sources/europe_pmc.py`
- Modify: `src/nature_academic_search/sources/semantic_scholar.py`

Add narrow relation methods that return normalized records/identifiers and never leak API keys. arXiv has no
relation method and remains explicitly skipped when requested.

### Task 4: Expose optional graph lookup through MCP

**Files:**
- Modify: `src/nature_academic_search/server.py`
- Modify: `tests/test_server.py`

Add optional `include_relations`, `relation`, `depth`, `rows`, and `relation_sources` parameters. Preserve
the old response byte shape when graph lookup is disabled.

### Task 5: Integrate workflow and documentation

**Files:**
- Modify: `src/nature_academic_search/workflow.py`
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `references/search-workflows.md`
- Modify: `references/workflows/wf1-multi-source-search.md`
- Modify: `tests/test_plugin_artifacts.py`
- Modify: `tests/test_release_metadata.py`

Add optional `expand_citations` workflow step/config and document graph JSON, source coverage, and safety
boundaries. Sync the packaged skill mirror.

### Task 6: Verify and publish

Run full pytest, Ruff, skill mirror check, `git diff --check`, package build/metadata checks, commit, push,
and verify GitHub CI for the pushed SHA. Keep user-owned `uv.lock` untracked.
