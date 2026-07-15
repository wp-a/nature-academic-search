# Academic Paper Search Brand Design

**Date:** 2026-07-15
**Status:** Approved

## Objective

Change the user-facing product name from **Nature Academic Search** to
**Academic Paper Search** while preserving every installed identifier and command.
The new name should immediately communicate that the project searches academic
papers, without forcing users to migrate packages, plugins, skills, MCP entries,
or repository URLs.

## Brand Model

Use two explicit layers:

- **Display brand:** `Academic Paper Search`
- **Technical identifier:** `nature-academic-search`

The display brand appears in user-facing headings, plugin UI metadata, package
descriptions, prompts, and repository metadata. The technical identifier remains
stable wherever software resolves, installs, invokes, or upgrades the project.

## Immutable Technical Identifiers

Do not rename any of the following:

- GitHub repository: `wp-a/nature-academic-search`
- PyPI project: `nature-academic-search`
- Python import package: `nature_academic_search`
- CLI command: `nature-academic-search`
- MCP entry point: `nature-academic-search-mcp`
- MCP server key: `nature-academic-search`
- skill name and invocation: `nature-academic-search` and
  `$nature-academic-search`
- plugin name: `nature-academic-search`
- marketplace name: `wp-a-academic-tools`

Existing installation commands, links, configurations, and upgrade paths must
continue to work unchanged.

## User-Facing Surfaces

Change the display brand consistently in:

1. README title and introductory copy.
2. Root and packaged `SKILL.md` headings.
3. Codex `agents/openai.yaml` `display_name`.
4. Codex plugin `interface.displayName` and user-facing descriptions.
5. Claude plugin and marketplace descriptions where a descriptive brand phrase
   is supported without changing their required identifier fields.
6. Python project description shown by PyPI package metadata.
7. GitHub repository description.
8. Release title and notes for version `0.1.2`.

The first README paragraph should state that `nature-academic-search` is the
technical package and plugin ID so users understand why install commands differ
from the visible brand.

## PyPI Policy

Keep PyPI as a low-maintenance runtime distribution, not as a separate brand or
marketing destination. It remains necessary because the plugin starts the pinned
runtime through:

```text
uvx --from nature-academic-search==<version> nature-academic-search-mcp
```

Publish to PyPI only when code, fixes, embedded skill behavior, or required
metadata changes. Do not create a second `academic-paper-search` distribution.
The one-time display-brand change requires `0.1.2` because the wheel embeds the
skill and Codex UI metadata.

## Release Scope

Release `0.1.2` as a metadata and branding patch:

- synchronize package, Python module, plugin manifests, Claude marketplace, and
  MCP pin versions;
- make no changes to search logic, source adapters, CLI commands, or MCP schemas;
- preserve the four MCP tools: `search_papers`, `get_paper_by_id`,
  `get_citation`, and `lookup_mesh`;
- state explicitly in release notes that there are no breaking identifier or API
  changes.

## Verification

The change is complete when:

- tests assert the new display brand on every supported UI surface;
- tests assert all technical identifiers remain unchanged;
- package and plugin versions are synchronized at `0.1.2`;
- root, plugin, and wheel-embedded skill content remains synchronized;
- Codex, Claude Code, and skill validators pass;
- wheel and sdist pass Twine validation;
- Codex and Claude Code marketplace installs report version `0.1.2`;
- a clean public PyPI install exposes the display brand in the embedded skill and
  still launches all four MCP tools through the unchanged commands;
- GitHub and PyPI release assets have matching SHA-256 digests.
