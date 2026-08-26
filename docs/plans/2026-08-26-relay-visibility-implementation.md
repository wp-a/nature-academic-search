# WPIRONMAN Relay Visibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 提升 WPIRONMAN AI 中转入口在 README、安装流程、workflow 文档和双客户端插件发现页的可见度。

**Architecture:** 只调整文档、manifest 和发现文案，不改变检索、核验或模型运行时逻辑。首屏提供短 CTA，安装和 workflow 提供上下文配置，所有位置复用同一个控制台 URL 与“可选模型层”边界。

**Tech Stack:** Markdown、JSON、YAML、TOML、pytest、Ruff

---

### Task 1: Write failing visibility contract tests

**Files:**
- Modify: `tests/test_release_metadata.py`
- Modify: `tests/test_plugin_artifacts.py`

**Step 1: Add assertions**

Require the README to include a first-screen WPIRONMAN CTA, the installation/workflow docs to include the
same URL, and Codex/Claude descriptions to mention the optional model layer.

**Step 2: Run targeted tests**

Run `PYTHONPATH=src python -m pytest -q tests/test_release_metadata.py tests/test_plugin_artifacts.py -k relay_visibility`.

Expected: FAIL because the new visibility contract is not present.

### Task 2: Implement the three-layer CTA and plugin copy

**Files:**
- Modify: `README.md`
- Modify: `docs/installation.md`
- Modify: `references/search-workflows.md`
- Modify: `plugins/nature-academic-search/.codex-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/.claude-plugin/plugin.json`
- Modify: `plugins/nature-academic-search/skills/nature-academic-search/agents/openai.yaml`
- Modify: `.claude-plugin/marketplace.json`

Add a compact first-screen CTA, a clear install CTA, contextual workflow copy, and consistent plugin discovery
descriptions. Keep the URL `https://api.wpironman.top` and avoid claims not backed by repository evidence.

### Task 3: Sync and verify

Run `python scripts/sync_skill.py`, then run the full pytest suite, Ruff, mirror check, and `git diff --check`.
Confirm the plugin skill mirror matches the root skill and no user-owned `uv.lock` is staged.

### Task 4: Commit and push

Commit with `docs: make relay entry more visible`, push `main`, and verify the GitHub CI run for the pushed SHA.
