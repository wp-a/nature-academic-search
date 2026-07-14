# PyPI and Plugin Redesign

## Goal

Publish `nature-academic-search` as a maintained Python package and as installable
Codex and Claude Code plugins while preserving the existing MCP tool names:
`search_papers`, `get_paper_by_id`, `get_citation`, and `lookup_mesh`.

## Success Criteria

- `pipx install nature-academic-search` and `uv tool install nature-academic-search`
  expose a working `nature-academic-search` CLI and MCP stdio server.
- One repository contains valid Codex and Claude Code plugin manifests backed by
  the same skill instructions and the published Python package.
- Existing `bash install.sh <PUBMED_EMAIL>` usage remains supported.
- Multi-source search actually deduplicates results and reports source-level
  failures without discarding successful results.
- Default tests are offline and deterministic. Network smoke tests are explicit.
- CI validates Python 3.10-3.13, package builds, MCP behavior, skill metadata,
  plugin manifests, and installer dry runs.
- A GitHub release can publish to PyPI through Trusted Publishing with provenance.

## Non-Goals

- Do not add databases beyond PubMed, CrossRef, and arXiv in the first release.
- Do not change the four public MCP tool names.
- Do not require a hosted MCP service.
- Do not promise unattended human maintenance; automate repeatable maintenance
  and document the remaining maintainer decisions.

## Repository Layout

```text
src/nature_academic_search/       # Published Python runtime
  cli.py                          # serve, install, preflight, citation commands
  server.py                       # FastMCP wiring and public tool contract
  sources/                        # PubMed, CrossRef, and arXiv adapters
  conversion/                     # RIS, BibTeX, NBIB, and ENW conversion
plugins/nature-academic-search/   # Distribution plugin
  .codex-plugin/plugin.json
  .claude-plugin/plugin.json
  .mcp.json
  SKILL.md
  agents/openai.yaml
  references/
.agents/plugins/marketplace.json  # Codex marketplace
.claude-plugin/marketplace.json   # Claude Code marketplace
tests/                            # Offline unit, contract, package, and install tests
docs/                             # User and maintainer documentation
```

The root `SKILL.md`, `references/`, and compatibility scripts remain for direct
skill installers. A sync test requires their contents to match the distributable
plugin skill so compatibility cannot silently drift.

## Runtime Contract

The server uses the stable MCP Python SDK v1 range, `mcp>=1.27,<2`, and runs over
stdio by default. Public tools continue returning JSON text for compatibility.
Changes to response objects are additive.

`search_papers` performs concurrent source calls and then normalizes and
deduplicates records in this order:

1. exact normalized DOI;
2. exact PMID;
3. exact normalized arXiv identifier;
4. normalized title plus publication year.

Merged records retain `sources`, all known identifiers, and the highest available
citation count. A source exception becomes an item in `errors`; successful source
results are still returned. The result reports both raw and deduplicated counts.

## CLI and Installation

The package exposes:

- `nature-academic-search serve` for the MCP stdio server;
- `nature-academic-search install --client codex|claude|both` for client setup;
- `nature-academic-search preflight` for explicit network diagnostics;
- `nature-academic-search citation` for citation file conversion;
- `nature-academic-search-mcp` as a compatibility-friendly server entry point.

The installer invokes the clients' supported CLIs instead of editing their config
files directly. It supports `--dry-run`, avoids global `pip install`, and preserves
the legacy positional email form in `install.sh`.

Plugin `.mcp.json` launches a release-pinned package through `uvx`. Users without
`uvx` receive an actionable error and can install the package through `pipx`.

## Plugin Packaging

The Codex plugin declares its skill folder and MCP companion file in
`.codex-plugin/plugin.json`. The Claude Code plugin uses the same components in
`.claude-plugin/plugin.json`. Both manifests use the package version and are
checked against `pyproject.toml` during CI.

Repository marketplaces point to `plugins/nature-academic-search`. The plugin
contains no secrets; PubMed email and optional API keys come from environment
variables at runtime.

## Error Handling

- Reject invalid source names and identifiers before network access.
- Bound rows and timeouts at the public interface.
- Preserve partial results when one source is unavailable.
- Return stable machine-readable error objects from MCP tools.
- Write logs to stderr only so stdio protocol output is never corrupted.
- Keep network diagnostics out of import-time and default test paths.

## Release and Maintenance

Use semantic versions beginning at `0.1.0`. The release workflow builds wheel and
sdist artifacts, verifies them with `twine check`, publishes through PyPI Trusted
Publishing, and attaches distributions to the GitHub release. Git tags, Python
package metadata, and plugin manifests must agree.

Maintenance automation includes:

- Dependabot for Python and GitHub Actions dependencies;
- a Python-version CI matrix;
- scheduled network smoke tests that do not block normal pull requests;
- release validation and package provenance;
- a concise maintainer release runbook.

The one external prerequisite is authorizing the GitHub workflow as a PyPI Trusted
Publisher for `wp-a/nature-academic-search`. If no publisher exists, the release
workflow must remain untriggered until that authorization is complete.

## Verification

1. Run existing tests before migration.
2. Add failing contract tests for deduplication, partial failures, tool names,
   manifests, installation commands, and package entry points.
3. Migrate implementation in small RED-GREEN-REFACTOR steps.
4. Build and install the wheel in a clean temporary environment.
5. Start an MCP client session, list all four tools, and call a no-network error
   path through stdio.
6. Validate both plugin manifests with current client CLIs where available.
7. Run explicit PubMed, CrossRef, and arXiv smoke tests.
8. Publish to TestPyPI when credentials are available, install that artifact, then
   create the production PyPI release and verify its public metadata.
