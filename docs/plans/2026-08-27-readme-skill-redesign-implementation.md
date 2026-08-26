# README 与 Skill 重构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重写中文优先 README，并完善 Codex/Claude Code skill，使六个科研场景、真实截图、引文图谱和 WPIRONMAN 可选中转都能被快速理解和正确使用。

**Architecture:** README 作为面向访客的转化入口，采用“价值 → 安装 → 复制任务 → 真实结果 → 能力与边界”的线性结构；SKILL.md 作为模型执行规范，采用“触发 → 路由 → 契约 → 风险”的短结构。详细事实和案例继续放在现有 docs/examples 与 references 中，插件目录通过 `scripts/sync_skill.py` 同步。

**Tech Stack:** Markdown、GitHub Markdown 图片/代码块、现有 Python 文档契约测试、`scripts/sync_skill.py`、Ruff、pytest、Hatch build。

---

### Task 1: 重写 README 信息架构

**Files:**
- Modify: `README.md`

**Step 1: 保留既有兼容性锚点**

保留项目名、安装标识 `nature-academic-search`、四个 MCP 工具名、Codex/Claude Code 安装命令、未连接数据库声明和 WPIRONMAN 控制台链接。

**Step 2: 建立中文用户首屏**

增加能力摘要和能力矩阵，把安装、最短 prompt、输出契约和首张真实截图前置。

**Step 3: 编排六个可复制场景**

为开题检索、AI 幻觉引用核验、PubMed/MeSH、上下游引文追踪、综述批量导出、临床试验关联核验分别提供 prompt、预期输出、边界；前三个场景嵌入已有真实截图。

**Step 4: 完善 WPIRONMAN 中转说明**

说明其是可选模型层，给出最小配置、适合的 plan/screen 用法、隐私默认值、失败降级和不具备的学术检索能力。

### Task 2: 重写 SKILL 执行规范

**Files:**
- Modify: `SKILL.md`
- Modify: `plugins/nature-academic-search/skills/nature-academic-search/SKILL.md`

**Step 1: 优化触发描述和任务路由**

覆盖中文科研检索、引用图谱、MeSH、workflow、导出和引用核验关键词；维持四工具约束。

**Step 2: 增加场景选择和中转边界**

明确何时使用 `include_relations`、何时使用 workflow，以及 WPIRONMAN 不属于学术来源。

**Step 3: 同步插件镜像**

运行 `python scripts/sync_skill.py`，确认根目录与插件 skill 一致。

### Task 3: 更新文档契约与验证

**Files:**
- Modify: `tests/test_plugin_artifacts.py` only if new stable phrases require explicit contract coverage
- Modify: `tests/test_release_metadata.py` only if README assertions need deliberate updates

**Step 1: 运行文档同步检查**

Run: `python scripts/sync_skill.py --check`

Expected: `Skill mirror is synchronized`

**Step 2: 运行静态检查和测试**

Run: `uv run --with 'ruff>=0.12,<1' ruff check src tests`

Run: `PYTHONPATH=src python -m pytest -q`

Expected: Ruff passes and all tests pass.

**Step 3: 构建发布产物**

Run: `uv run --with 'build>=1.3,<2' python -m build --outdir <temporary-directory>`

Expected: sdist and wheel build successfully.

**Step 4: Commit**

```bash
git add README.md SKILL.md plugins/nature-academic-search/skills/nature-academic-search/SKILL.md docs/plans/2026-08-27-readme-skill-redesign-*.md
git commit -m "docs: redesign readme and skill for research workflows"
```
