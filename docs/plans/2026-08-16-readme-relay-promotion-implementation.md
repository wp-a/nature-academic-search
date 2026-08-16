# README Relay Promotion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a transparent WPIRONMAN AI relay promotion after the README installation instructions without displacing the paper-search product story.

**Architecture:** Treat the promotion as tested README content. A metadata test locks the disclosure, destination, factual copy, and section ordering; the implementation adds one GitHub-native `TIP` callout and no new assets or runtime behavior.

**Tech Stack:** Markdown, Python, pytest

---

### Task 1: Add the disclosed relay promotion

**Files:**
- Modify: `tests/test_release_metadata.py`
- Modify: `README.md`

**Step 1: Write the failing test**

Add this test to `tests/test_release_metadata.py` after the installation-path test:

```python
def test_readme_discloses_relay_promotion_after_installation() -> None:
    readme = read("README.md")

    promotion = "> **推广 · WPIRONMAN AI 中转控制台**"
    for required in (
        "> [!TIP]",
        promotion,
        "统一管理模型渠道、密钥、额度与调用入口",
        "[进入控制台 →](https://api.wpironman.top)",
    ):
        assert required in readme

    assert readme.index("## 30 秒开始") < readme.index(promotion)
    assert readme.index(promotion) < readme.index("## 数据源如何分工")
```

**Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=src python -m pytest -q tests/test_release_metadata.py -k relay_promotion
```

Expected: FAIL because the promotion disclosure is not yet present in `README.md`.

**Step 3: Add the minimal README callout**

Insert this block after the installation credential paragraph and before
`## 数据源如何分工`:

```markdown
> [!TIP]
> **推广 · WPIRONMAN AI 中转控制台**
>
> 统一管理模型渠道、密钥、额度与调用入口，让模型服务状态更清晰。
> [进入控制台 →](https://api.wpironman.top)
```

Do not add pricing, speed, uptime, discount, or client-compatibility claims.

**Step 4: Run the targeted test to verify it passes**

Run:

```bash
PYTHONPATH=src python -m pytest -q tests/test_release_metadata.py -k relay_promotion
```

Expected: `1 passed`.

**Step 5: Run repository verification**

Run:

```bash
PYTHONPATH=src python -m pytest -q
python scripts/sync_skill.py --check
git diff --check
```

Expected: all tests pass, the skill mirror is synchronized, and no whitespace
errors are reported. The GitHub CI lint job supplies the canonical Ruff check.

**Step 6: Commit and push**

```bash
git add README.md tests/test_release_metadata.py
git commit -m "docs: promote WPIRONMAN AI relay"
git push origin main
```

Leave the user-owned untracked `uv.lock` unchanged and wait for the pushed CI
run to complete.
