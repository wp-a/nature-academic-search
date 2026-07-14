# PyPI and Plugin Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publish `nature-academic-search` as a tested Python package and dual Codex/Claude Code plugin without breaking its four MCP tool names.

**Architecture:** Move runtime code into a standard `src/nature_academic_search` package, expose a CLI and stdio MCP server, and keep plugin artifacts as thin release-pinned clients of that package. Make contracts executable through offline tests and publish with GitHub Actions Trusted Publishing.

**Tech Stack:** Python 3.10+, MCP Python SDK v1, pytest, hatchling, Ruff, GitHub Actions, PyPI Trusted Publishing, Codex and Claude Code plugin manifests.

---

### Task 1: Establish the Python Package Contract

**Files:**
- Create: `pyproject.toml`
- Create: `src/nature_academic_search/__init__.py`
- Create: `src/nature_academic_search/__main__.py`
- Create: `tests/test_package_metadata.py`
- Create: `.gitignore`

**Step 1: Write the failing test**

Assert that the package imports, exposes `__version__ == "0.1.0"`, declares Python
3.10+, pins `mcp` below v2, and defines both console scripts.

**Step 2: Verify RED**

Run: `python -m pytest tests/test_package_metadata.py -q`

Expected: FAIL because `pyproject.toml` and the import package do not exist.

**Step 3: Implement the minimum package skeleton**

Use hatchling with this dependency boundary:

```toml
dependencies = [
  "mcp>=1.27,<2",
  "requests>=2.28,<3",
  "toml>=0.10.2,<1",
]

[project.scripts]
nature-academic-search = "nature_academic_search.cli:main"
nature-academic-search-mcp = "nature_academic_search.server:main"
```

**Step 4: Verify GREEN**

Run: `python -m pytest tests/test_package_metadata.py -q`

Expected: PASS.

**Step 5: Commit**

Commit message: `build: scaffold distributable Python package`

### Task 2: Migrate Sources and Conversion Utilities

**Files:**
- Create: `src/nature_academic_search/sources/*.py`
- Create: `src/nature_academic_search/config.py`
- Create: `src/nature_academic_search/errors.py`
- Create: `src/nature_academic_search/logging.py`
- Create: `src/nature_academic_search/conversion/*.py`
- Create: `tests/test_sources.py`
- Create: `tests/test_conversion.py`
- Modify: `mcp-server/*` compatibility wrappers
- Modify: `scripts/format-converter.py`

**Step 1: Move existing mocked source tests to package imports**

Keep HTTP fully mocked. Add tests proving imports no longer depend on the current
working directory and logging setup does not duplicate handlers.

**Step 2: Verify RED**

Run: `python -m pytest tests/test_sources.py tests/test_conversion.py -q`

Expected: FAIL because package modules are absent.

**Step 3: Migrate the minimum runtime code**

Use package-relative imports, `importlib.resources` or environment defaults for
configuration, and compatibility wrappers for old script paths.

**Step 4: Verify GREEN**

Run the new tests and the legacy `mcp-server/tests` suite. Expected: all PASS.

**Step 5: Commit**

Commit message: `refactor: move academic sources into package`

### Task 3: Implement the Search Contract and Deduplication

**Files:**
- Create: `src/nature_academic_search/search.py`
- Create: `tests/test_search.py`
- Modify: `src/nature_academic_search/server.py`

**Step 1: Write failing behavior tests**

Cover DOI, PMID, arXiv, and title/year duplicate keys; source provenance merging;
highest citation count selection; deterministic ordering; and partial source
failures.

```python
def test_duplicate_doi_records_merge_sources():
    merged = deduplicate_records([
        {"doi": "10.1/ABC", "source": "crossref", "citation_count": 3},
        {"doi": "https://doi.org/10.1/abc", "source": "pubmed", "citation_count": 5},
    ])
    assert len(merged) == 1
    assert merged[0]["sources"] == ["crossref", "pubmed"]
    assert merged[0]["citation_count"] == 5
```

**Step 2: Verify RED**

Run: `python -m pytest tests/test_search.py -q`

Expected: FAIL because no deduplication module exists.

**Step 3: Implement minimal normalization and merging**

Keep the current tool response fields and add `raw_result_count`, `result_count`,
`sources_queried`, and `errors`.

**Step 4: Verify GREEN**

Run search tests and all source tests. Expected: PASS.

**Step 5: Commit**

Commit message: `feat: deduplicate multi-source search results`

### Task 4: Build the MCP Server and CLI

**Files:**
- Create: `src/nature_academic_search/server.py`
- Create: `src/nature_academic_search/cli.py`
- Create: `tests/test_server.py`
- Create: `tests/test_cli.py`
- Modify: `mcp-server/academic_search_server.py`

**Step 1: Write failing contract tests**

Assert exactly the four legacy tool names, input validation before network calls,
stderr-only logging, `serve`, `preflight`, `citation`, and `install --dry-run`.

**Step 2: Verify RED**

Run: `python -m pytest tests/test_server.py tests/test_cli.py -q`

Expected: FAIL because the entry points do not exist.

**Step 3: Implement the minimal CLI and server wiring**

Use `from mcp.server.fastmcp import FastMCP` and `mcp.run(transport="stdio")`.
Keep tool results as JSON text for backward compatibility.

**Step 4: Verify GREEN**

Run CLI and server tests, then start an MCP client session and list tools.

**Step 5: Commit**

Commit message: `feat: expose package CLI and stdio MCP server`

### Task 5: Package the Codex and Claude Code Plugins

**Files:**
- Create: `plugins/nature-academic-search/.codex-plugin/plugin.json`
- Create: `plugins/nature-academic-search/.claude-plugin/plugin.json`
- Create: `plugins/nature-academic-search/.mcp.json`
- Create: `plugins/nature-academic-search/SKILL.md`
- Create: `plugins/nature-academic-search/agents/openai.yaml`
- Create: `.agents/plugins/marketplace.json`
- Create: `.claude-plugin/marketplace.json`
- Modify: `SKILL.md`
- Modify: `references/*.md`
- Create: `tests/test_plugin_artifacts.py`

**Step 1: Write failing manifest and skill tests**

Assert manifest names and versions match the package, referenced paths exist,
`.mcp.json` pins the same package version, root and plugin skill content match,
and SKILL frontmatter is valid.

**Step 2: Verify RED**

Run: `python -m pytest tests/test_plugin_artifacts.py -q`

Expected: FAIL because plugin artifacts do not exist.

**Step 3: Scaffold and customize plugin files**

Use the Codex plugin scaffold helper and current `claude plugin init` output as the
schema sources. Keep bundled skill instructions under 500 words and route detailed
workflows to references.

**Step 4: Verify GREEN**

Run pytest plus Codex and Claude plugin validators. Expected: PASS.

**Step 5: Commit**

Commit message: `feat: add Codex and Claude Code plugins`

### Task 6: Replace the Legacy Installer Safely

**Files:**
- Modify: `install.sh`
- Create: `tests/test_installer.py`
- Modify: `config/*`

**Step 1: Write failing installer tests**

Use temporary homes and stub `codex`/`claude` executables. Verify `--client`,
`--dry-run`, legacy positional email, no global pip call, and idempotent MCP
registration commands.

**Step 2: Verify RED**

Run: `python -m pytest tests/test_installer.py -q`

Expected: FAIL against the current installer.

**Step 3: Implement the compatibility installer**

Delegate package setup to `uv tool install` or `pipx install`, then register the
stdio server through each client's CLI. Do not edit config JSON/TOML directly.

**Step 4: Verify GREEN**

Run installer tests and manual `--dry-run` for Codex, Claude, and both.

**Step 5: Commit**

Commit message: `fix: make dual-client installation isolated and idempotent`

### Task 7: Add Release and Maintenance Automation

**Files:**
- Create: `LICENSE`
- Modify: `README.md`
- Create: `docs/installation.md`
- Create: `docs/maintenance.md`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/publish.yml`
- Create: `.github/workflows/network-smoke.yml`
- Create: `.github/dependabot.yml`
- Create: `tests/test_release_metadata.py`

**Step 1: Write failing release consistency tests**

Assert package, plugin, workflow, and documentation versions/names agree and
release workflow uses OIDC with `id-token: write` and no PyPI password secret.

**Step 2: Verify RED**

Run: `python -m pytest tests/test_release_metadata.py -q`

Expected: FAIL because release files do not exist.

**Step 3: Add minimal automation and documentation**

Use PyPA build/twine tooling and `pypa/gh-action-pypi-publish` with the `pypi`
GitHub environment.

**Step 4: Verify GREEN**

Run all offline tests, Ruff, package build, and `twine check`.

**Step 5: Commit**

Commit message: `ci: automate testing and trusted PyPI releases`

### Task 8: End-to-End Release Verification

**Files:**
- Modify only files required by failures found during verification.

**Step 1: Install the built wheel in a clean environment**

Run CLI help, preflight help, and MCP tool listing from the installed artifact.

**Step 2: Validate plugins with current clients**

Run Codex plugin validator and `claude plugin validate --strict`.

**Step 3: Run explicit network smoke tests**

Verify one known PubMed record, one CrossRef DOI, and one arXiv identifier.

**Step 4: Configure release infrastructure**

Create the GitHub `pypi` environment. Confirm the PyPI Trusted Publisher mapping:
owner `wp-a`, repository `nature-academic-search`, workflow `publish.yml`,
environment `pypi`.

**Step 5: Publish and verify**

Publish `v0.1.0`, install from public PyPI, verify package metadata and all four
MCP tools, and confirm GitHub release artifacts.

**Step 6: Final commit**

Commit message: `release: prepare nature-academic-search 0.1.0`
