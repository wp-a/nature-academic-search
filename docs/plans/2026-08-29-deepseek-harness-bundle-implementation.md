# DeepSeek Harness Bundle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publish-ready npm Bundle metadata and documentation that installs the existing Academic Paper Search MCP server into DeepSeek Harness without duplicating search logic.

**Architecture:** Add a thin package under `plugins/dsh-academic-paper-search`. Its `dsh.bundle.patch` inserts the official `@deepseek-ai/dsh-mcp-client` with a stdio configuration that launches the pinned PyPI MCP entry point via `uvx`. Update the Python project's public positioning and tests to make the third-client compatibility explicit.

**Tech Stack:** npm package metadata, Cordis YAML patch, Node ESM, Python pytest/PyYAML/TOML metadata tests, Ruff, hatchling.

---

### Task 1: Add failing Bundle contract tests

**Files:**
- Create: `tests/test_deepseek_bundle.py`

**Step 1: Write the failing test**

Assert the package name, `dsh.bundle.patch`, pinned runtime dependency, patch row id, `academic_search` namespace, `uvx` arguments, and explicit environment forwarding expressions.

**Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_deepseek_bundle.py`

Expected: FAIL because `plugins/dsh-academic-paper-search/` does not yet exist.

### Task 2: Create the minimal DSH npm Bundle

**Files:**
- Create: `plugins/dsh-academic-paper-search/package.json`
- Create: `plugins/dsh-academic-paper-search/index.js`
- Create: `plugins/dsh-academic-paper-search/cordis.patch.yml`
- Create: `plugins/dsh-academic-paper-search/README.md`
- Create: `plugins/dsh-academic-paper-search/README.zh.md`

**Step 1: Implement the package manifest**

Use package name `dsh-academic-paper-search`, version `0.1.0`, `type: module`,
`main: ./index.js`, `files`, `engines.node >=22.19.0`, exact
`@deepseek-ai/dsh-mcp-client` dependency `0.1.1-rc.2`, and the official
`dsh.bundle.patch` field.

**Step 2: Implement the Bundle patch**

Insert `academic-search-mcp` with `@deepseek-ai/dsh-mcp-client`, stdio transport,
server name `academic_search`, `uvx` command and pinned `nature-academic-search==0.3.0`.
Forward supported environment variables with nullish-empty JavaScript expressions;
set startup failure to non-fatal and enable bounded reconnect.

**Step 3: Document installation and boundaries**

Provide Chinese-first examples for web/headless profiles, `PUBMED_EMAIL`, optional
credentials, tool namespace, source roles, DSH preview warning, and the fact that
the bridge does not replace academic sources or the optional WPIRONMAN relay.

**Step 4: Run the focused test**

Run: `python -m pytest -q tests/test_deepseek_bundle.py`

Expected: PASS.

### Task 3: Update project descriptions and installation docs

**Files:**
- Modify: `README.md`
- Modify: `docs/installation.md`
- Modify: `pyproject.toml`
- Modify: `plugins/nature-academic-search/.codex-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.agents/plugins/marketplace.json`

**Step 1: Add the third-client positioning**

Use “Codex / Claude Code / DeepSeek Harness” in the public description, link the
official DSH install path, explain the `dsh-academic-paper-search` companion package,
and preserve the existing `nature-academic-search` technical install id.

**Step 2: Run metadata and README tests**

Run: `python -m pytest -q tests/test_plugin_artifacts.py tests/test_release_metadata.py tests/test_deepseek_bundle.py`

Expected: PASS.

### Task 4: Validate package and existing repository

**Step 1: Validate JSON/YAML and package contents**

Run: `python -m pytest -q tests/test_deepseek_bundle.py`; inspect `npm pack --dry-run`
with the package directory as cwd; run the repository plugin validator where available.

**Step 2: Run full verification**

Run: `python -m pytest -q && ruff check . && python -m build && twine check dist/*`

Expected: all tests pass, Ruff clean, wheel/sdist build succeeds, and metadata checks pass.

**Step 3: Commit**

```bash
git add README.md docs/installation.md pyproject.toml \
  plugins/dsh-academic-paper-search \
  plugins/nature-academic-search/.codex-plugin/plugin.json \
  plugins/nature-academic-search/.claude-plugin/plugin.json \
  .claude-plugin/marketplace.json .agents/plugins/marketplace.json \
  tests/test_deepseek_bundle.py docs/plans/2026-08-29-deepseek-harness-bundle-design.md \
  docs/plans/2026-08-29-deepseek-harness-bundle-implementation.md
git commit -m "feat: add DeepSeek Harness academic search bundle"
```
