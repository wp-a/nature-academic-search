# README and Skill Star Conversion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite the Chinese-first README and skill so researchers can understand, try, and trust the project quickly, then make the repository discoverable through accurate GitHub metadata.

**Architecture:** Keep the implementation content-only: preserve the four MCP tools and package behavior, add contract tests for the approved messaging, keep both skill copies identical, and update GitHub metadata through `gh`. Use progressive disclosure so the README sells the workflow while detailed installation and maintenance remain in existing docs.

**Tech Stack:** Markdown, YAML frontmatter, pytest content-contract tests, GitHub CLI, Codex and Claude Code skill/plugin validators.

---

### Task 1: Add README and skill conversion contracts

**Files:**
- Modify: `tests/test_release_metadata.py`
- Modify: `tests/test_plugin_artifacts.py`

**Step 1: Write the failing README contract test**

Add a test that requires the README to contain the approved Chinese value
proposition, a copy-ready prompt, the reproducible workflow stages, an explicit
unsupported-source boundary, all three installation paths, and a restrained star
call to action.

```python
def test_readme_presents_the_chinese_research_workflow() -> None:
    readme = read("README.md")

    for required in (
        "可复现的文献检索、核验与引用导出",
        "直接这样问",
        "检索 → 去重 → 核验 → 导出",
        "Google Scholar",
        "Codex",
        "Claude Code",
        "如果这个项目",
    ):
        assert required in readme
```

**Step 2: Write the failing skill contract test**

Extend the existing synchronized-skill test or add a focused test requiring
Chinese trigger phrases, task routing, the four verification states, the result
report contract, and both reference links.

```python
def test_skill_routes_chinese_research_requests_and_reports_verification() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    for required in (
        "找文献",
        "文献检索",
        "任务路由",
        "verified",
        "mismatch",
        "not_found",
        "manual_needed",
        "结果契约",
        "references/search-workflows.md",
        "references/citation-files.md",
    ):
        assert required in skill
```

**Step 3: Run the focused tests and verify they fail**

Run:

```bash
python -m pytest tests/test_release_metadata.py tests/test_plugin_artifacts.py -v
```

Expected: the new README and skill contract tests fail because the approved
Chinese sections do not exist yet; existing tests continue to pass.

**Step 4: Commit the red tests**

```bash
git add tests/test_release_metadata.py tests/test_plugin_artifacts.py
git commit -m "test: define README and skill conversion contracts"
```

### Task 2: Rewrite the skill for Chinese research workflows

**Files:**
- Modify: `SKILL.md`
- Modify: `plugins/nature-academic-search/skills/nature-academic-search/SKILL.md`
- Reference: `references/search-workflows.md`
- Reference: `references/citation-files.md`

**Step 1: Rewrite the root skill**

Keep valid YAML frontmatter with the existing name. Expand the description with
Chinese request phrases and preserve English triggers. Organize the body into:

1. operating principle;
2. task routing table;
3. source boundary;
4. staged workflow;
5. verification states;
6. result contract;
7. Chinese prompt examples;
8. evidence rules and progressive-disclosure references.

Keep the body below the existing 600-word contract and do not promise unsupported
sources or full-text access.

**Step 2: Apply the identical content to the plugin skill**

Use `apply_patch` for both files and verify byte equality:

```bash
cmp SKILL.md plugins/nature-academic-search/skills/nature-academic-search/SKILL.md
```

Expected: exit code 0 with no output.

**Step 3: Run the focused plugin tests**

Run:

```bash
python -m pytest tests/test_plugin_artifacts.py -v
```

Expected: all plugin tests pass, including synchronization, word-count, reference,
and Chinese workflow contracts.

**Step 4: Run skill and plugin validators**

Use the exact validators identified by `skill-creator`, `writing-skills`, and
`plugin-creator`. Also run:

```bash
claude plugin validate --strict plugins/nature-academic-search
```

Expected: every available validator exits 0. If a client validator is unavailable,
record the missing command and rely on its corresponding content-contract tests.

**Step 5: Commit the skill rewrite**

```bash
git add SKILL.md plugins/nature-academic-search/skills/nature-academic-search/SKILL.md
git commit -m "docs: route Chinese academic search workflows"
```

### Task 3: Rewrite the Chinese-first README

**Files:**
- Modify: `README.md`
- Reference: `docs/installation.md`
- Reference: `docs/maintenance.md`

**Step 1: Replace the first-screen narrative**

Add the approved Chinese value proposition, compact badges, a copy-ready research
prompt, a clearly labeled illustrative result contract, and the shortest valid
Codex/Claude/CLI quick-start paths.

**Step 2: Add the workflow and capability sections**

Document `检索 → 去重 → 核验 → 导出`, add a PubMed/CrossRef/arXiv capability
matrix, explain verification-first differentiation, and state unsupported sources
and partial-failure behavior explicitly.

**Step 3: Add use cases, tools, trust boundaries, and contribution CTA**

Include Chinese prompt examples for discovery, MeSH strategy, citation
verification, preprint checking, and export. Preserve all current supported
commands. Link to installation, maintenance, releases, issues, and the MIT license.

**Step 4: Run the README tests**

Run:

```bash
python -m pytest tests/test_release_metadata.py -v
```

Expected: all release metadata and README content-contract tests pass.

**Step 5: Commit the README rewrite**

```bash
git add README.md
git commit -m "docs: make the research workflow visible first"
```

### Task 4: Update and verify GitHub discovery metadata

**Files:**
- No repository file changes

**Step 1: Update description and homepage**

Run `gh repo edit wp-a/nature-academic-search` with this approved description:

```text
面向中文科研用户的 Codex / Claude Code 学术检索 Skill + MCP：跨 PubMed、CrossRef、arXiv 检索、去重、核验并导出引用。
```

Set the homepage to:

```text
https://pypi.org/project/nature-academic-search/
```

**Step 2: Add focused repository topics**

Add exactly these topics unless GitHub rejects a reserved or invalid value:

```text
academic-search literature-review citation-management pubmed crossref arxiv mcp codex claude-code research-tools
```

**Step 3: Read back the public metadata**

Run:

```bash
gh repo view wp-a/nature-academic-search --json description,homepageUrl,repositoryTopics
```

Expected: description and homepage match exactly and all ten topics are present.

### Task 5: Run full verification and publish the repository changes

**Files:**
- Verify: all changed and packaged files

**Step 1: Run formatting and content checks**

```bash
python -m ruff check src tests
python -m pytest
python -m pytest mcp-server/tests
```

Expected: Ruff passes, 38 or more package tests pass after the new contracts, and
all 31 legacy MCP tests pass.

**Step 2: Build and validate distributions**

```bash
python -m build
twine check dist/*
```

Expected: wheel and sdist build successfully and pass Twine validation. Confirm
the wheel contains the rewritten embedded skill and both referenced files.

**Step 3: Verify links and repository state**

Check relative README and skill links against the filesystem, inspect `git diff
--check`, and confirm no generated or unrelated files are staged.

**Step 4: Review the complete commit range**

```bash
git log --oneline ffc93ff..HEAD
git diff --stat ffc93ff..HEAD
```

Expected: only the design, plan, tests, README, and synchronized skill files are
changed locally; remote metadata is verified separately.

**Step 5: Push and verify CI**

```bash
git push origin main
gh run watch --exit-status
```

Expected: the post-push CI matrix and build job complete successfully.
