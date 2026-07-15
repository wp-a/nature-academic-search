# Academic Paper Search Brand Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply the `Academic Paper Search` display brand without changing any technical identifier, then publish the synchronized branding metadata and embedded skill as version `0.1.2`.

**Architecture:** Treat display brand and technical identity as separate contracts. Content tests protect every user-facing brand surface while existing package and plugin tests preserve `nature-academic-search` identifiers; a second TDD cycle synchronizes the patch version before the normal PR, OIDC, and public-install release gates.

**Tech Stack:** Markdown, JSON, YAML, TOML, pytest, Hatchling, Twine, GitHub CLI, PyPI Trusted Publishing, Codex and Claude Code plugin validators.

---

### Task 1: Define the display-brand and identifier contracts

**Files:**
- Modify: `tests/test_release_metadata.py`
- Modify: `tests/test_plugin_artifacts.py`

**Step 1: Add a failing package and README brand test**

Define:

```python
DISPLAY_BRAND = "Academic Paper Search"
TECHNICAL_ID = "nature-academic-search"
```

Add assertions that:

- `README.md` contains `# Academic Paper Search` and explains that
  `nature-academic-search` remains the technical package and plugin ID;
- the project name and both script names remain unchanged;
- the project description starts with the display brand;
- the README no longer presents `Nature Academic Search` as the current product
  name.

**Step 2: Add a failing plugin and skill brand test**

Require both synchronized skill files to use `# Academic Paper Search`, while
their YAML `name` remains `nature-academic-search`. Require:

```python
assert codex_manifest["name"] == TECHNICAL_ID
assert codex_manifest["interface"]["displayName"] == DISPLAY_BRAND
assert claude_manifest["name"] == TECHNICAL_ID
assert openai_interface["display_name"] == DISPLAY_BRAND
```

Also require the Codex/Claude manifest descriptions and Claude marketplace plugin
description to include `Academic Paper Search`.

**Step 3: Run the focused tests and verify RED**

```bash
python -m pytest tests/test_release_metadata.py tests/test_plugin_artifacts.py -v
```

Expected: only the new display-brand assertions fail; existing identifier and
plugin structure tests pass.

**Step 4: Commit the failing contracts**

```bash
git add tests/test_release_metadata.py tests/test_plugin_artifacts.py
git commit -m "test: define Academic Paper Search brand contract"
```

### Task 2: Apply the display brand without renaming identifiers

**Files:**
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `pyproject.toml`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/nature-academic-search/.codex-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/.claude-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/skills/nature-academic-search/SKILL.md`
- Modify: `plugins/nature-academic-search/skills/nature-academic-search/agents/openai.yaml`

**Step 1: Update README branding**

Change the H1 and comparison table header to `Academic Paper Search`. Add one
short sentence below the value proposition:

```text
安装标识仍为 `nature-academic-search`，现有命令与配置无需迁移。
```

Do not alter installation commands, repository links, CLI names, MCP names, or
skill invocation examples.

**Step 2: Update synchronized skill headings and UI metadata**

Change only the Markdown headings in both skill files to `Academic Paper Search`.
Regenerate or update `agents/openai.yaml` so `display_name` is the new brand;
preserve `$nature-academic-search` in `default_prompt` and preserve YAML skill
`name: nature-academic-search`.

**Step 3: Update package and plugin descriptions**

Prefix the Python package, Codex plugin, Claude plugin, and Claude marketplace
plugin descriptions with `Academic Paper Search`. Change Codex
`interface.displayName` to the new brand. Do not change any JSON `name`, source,
marketplace, entry-point, or MCP key.

**Step 4: Run focused tests and validators**

```bash
python -m pytest tests/test_release_metadata.py tests/test_plugin_artifacts.py -v
python /Users/wangpeng/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/nature-academic-search/skills/nature-academic-search
python /Users/wangpeng/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/nature-academic-search
claude plugin validate --strict plugins/nature-academic-search
```

Expected: every command exits 0, the two skill files compare equal, and all
technical identifiers remain unchanged.

**Step 5: Commit the display brand**

```bash
git add README.md SKILL.md pyproject.toml .claude-plugin/marketplace.json plugins/nature-academic-search
git commit -m "docs: present Academic Paper Search brand"
```

### Task 3: Prepare the synchronized 0.1.2 patch release

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_package_metadata.py`
- Modify: `tests/test_release_metadata.py`
- Modify: `pyproject.toml`
- Modify: `src/nature_academic_search/__init__.py`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/nature-academic-search/.codex-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/.claude-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/.mcp.json`
- Modify: `docs/maintenance.md`

**Step 1: Change tests to expect 0.1.2**

Update the hard-coded CLI, package, and release contract version from `0.1.1`
to `0.1.2`. Run:

```bash
python -m pytest tests/test_cli.py tests/test_package_metadata.py tests/test_release_metadata.py tests/test_plugin_artifacts.py -v
```

Expected: version assertions fail because production files still report `0.1.1`.

**Step 2: Synchronize every versioned surface**

Set `0.1.2` in the Python project, module, both plugin manifests, Claude
marketplace metadata, and MCP `uvx` package pin. Keep the Codex marketplace
unchanged because it has no version field.

**Step 3: Record the low-maintenance PyPI policy**

State in `docs/maintenance.md` that PyPI remains the pinned plugin runtime and is
published only for code, fixes, embedded skill behavior, or required metadata.
Make TestPyPI conditional on its separate Trusted Publisher being configured;
otherwise require clean-wheel and PR-build evidence and record the skip.

**Step 4: Run the focused tests and verify GREEN**

Run the focused command from Step 1 again. Expected: all tests pass.

**Step 5: Commit the release preparation**

```bash
git add tests pyproject.toml src/nature_academic_search/__init__.py .claude-plugin/marketplace.json plugins/nature-academic-search docs/maintenance.md
git commit -m "release: prepare Academic Paper Search 0.1.2"
```

### Task 4: Run release gates and verify built artifacts

**Files:**
- Verify all packaged and plugin files

**Step 1: Run local gates**

```bash
python -m ruff check src tests
python -m pytest
python -m pytest mcp-server/tests
nature-academic-search preflight
```

Expected: Ruff passes, at least 40 package tests pass, all 31 legacy tests pass,
and PubMed/CrossRef/arXiv are reachable.

**Step 2: Run skill and plugin validators again**

Run the three validator commands from Task 2. Expected: all pass.

**Step 3: Build outside the repository and validate**

```bash
python -m build --outdir /tmp/nature-academic-search-012-dist
twine check /tmp/nature-academic-search-012-dist/*
```

Verify wheel metadata reports project `nature-academic-search`, version `0.1.2`,
and the description brand `Academic Paper Search`. Compare the wheel-embedded
SKILL and `agents/openai.yaml` byte-for-byte with repository sources.

**Step 4: Install the local wheel in a clean environment**

Verify unchanged CLI and stdio MCP entry points, version `0.1.2`, the embedded
display brand, and exactly four MCP tools.

**Step 5: Audit the branch**

Run `git diff --check`, inspect every changed file, and confirm no current product
surface still presents `Nature Academic Search` except the approved historical
design record.

### Task 5: Integrate through PR and update GitHub metadata

**Files:**
- No additional repository files expected

**Step 1: Push and create a pull request**

Push `brand/academic-paper-search-0.1.2`, create a PR against `main`, and include
the display-brand boundary, unchanged IDs, local gates, and release plan.

**Step 2: Wait for both push and pull-request CI runs**

Require Python 3.10–3.13 and build jobs to pass. Merge only after all required
checks are green.

**Step 3: Synchronize local main and verify merge CI**

Pull `main`, verify its package version and display brand, and wait for its push
CI run.

**Step 4: Update GitHub description**

Set a Chinese-first description beginning with `Academic Paper Search` while
retaining `Codex`, `Claude Code`, `MCP`, `PubMed`, `CrossRef`, and `arXiv` search
keywords. Read it back through the GitHub API.

### Task 6: Publish and verify version 0.1.2

**Files:**
- No further source changes expected

**Step 1: Confirm release uniqueness**

Verify PyPI `0.1.2`, GitHub Release `v0.1.2`, and tag `v0.1.2` do not exist.

**Step 2: Create and inspect a draft GitHub Release**

Target the merged `main` commit. Release notes must state the display-brand
change, unchanged technical IDs and commands, PyPI runtime role, and no breaking
API change.

**Step 3: Publish and watch production OIDC**

Publish the draft and require build, PyPI Trusted Publishing, attestations, and
GitHub Release asset upload to pass. Do not dispatch TestPyPI because its
independent Trusted Publisher is known to be unconfigured.

**Step 4: Verify public distribution**

Compare PyPI and GitHub Release SHA-256 digests. Install
`nature-academic-search==0.1.2` without cache in a clean environment and verify:

- CLI reports `0.1.2`;
- packaged skill displays `Academic Paper Search`;
- PubMed, CrossRef, and arXiv preflight succeeds;
- stdio and pinned `uvx` expose exactly four MCP tools;
- Codex and Claude Code marketplace installs report `0.1.2` while retaining
  plugin ID `nature-academic-search`.

**Step 5: Clean up and audit final state**

Remove the merged worktree and local branch. Confirm `main` equals `origin/main`,
HEAD is tagged `v0.1.2`, the public release is not a draft/prerelease, and PyPI
lists wheel and sdist files.
