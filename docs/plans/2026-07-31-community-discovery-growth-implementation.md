# Academic Paper Search Community Discovery Growth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn Academic Paper Search's working v0.2.0 product into a Chinese-first, evidence-backed discovery funnel and submit it to 8-12 relevant third-party catalogs.

**Architecture:** Keep the product repository as the canonical evidence and installation surface, and use WPIRONMAN posts as task-specific acquisition pages. Generate screenshots only from saved live outputs, then submit concise target-specific metadata to external catalogs and record the resulting URLs and status.

**Tech Stack:** Python/pytest, Markdown, Hexo/Butterfly, Node test runner, Playwright browser QA, GitHub CLI and GitHub Actions.

---

### Task 1: Define the repository growth contract

**Files:**
- Modify: `tests/test_release_metadata.py`
- Create: `docs/community-growth.md`
- Create: `docs/community-submissions.md`

**Steps:**

1. Add failing assertions for the three Chinese use cases, real-result asset references, current seven-source positioning, and community-growth documents.
2. Run `PYTHONPATH=src python -m pytest tests/test_release_metadata.py -q` and confirm the new assertions fail.
3. Add the metric definitions, 2026-07-31 baseline, monthly measurement commands, and submission ledger schema.
4. Re-run the focused test and confirm it passes after the remaining repository assets land.
5. Commit as `test: define community discovery growth contract`.

### Task 2: Produce reproducible real-result examples

**Files:**
- Create: `docs/examples/topic-scoping.md`
- Create: `docs/examples/citation-verification.md`
- Create: `docs/examples/pubmed-mesh.md`
- Create: `docs/assets/academic-search-topic-scoping.png`
- Create: `docs/assets/academic-search-citation-verification.png`
- Create: `docs/assets/academic-search-pubmed-mesh.png`

**Steps:**

1. Run the current v0.2.0 implementation against live sources for one bounded query per scenario.
2. Save only the compact, source-grounded fields needed to reproduce each result; include UTC/Asia-Shanghai date, query, identifiers, source status, and limitations.
3. Render local HTML views of the saved outputs and capture 1440px desktop screenshots; do not fabricate counts or successful sources.
4. Inspect each image and confirm text is readable, identifiers match the saved output, and no secrets appear.
5. Add tests that reject placeholder markers and zero-byte images, then run the focused test.
6. Commit as `docs: add reproducible academic search examples`.

### Task 3: Improve the canonical repository landing surface

**Files:**
- Modify: `README.md`
- Modify: `docs/installation.md` only if the landing path references stale installation behavior
- Modify: `tests/test_release_metadata.py`

**Steps:**

1. Add the real-result visual near the first decision path and a compact link to all three examples.
2. Add three copyable Chinese prompts with explicit evidence boundaries.
3. Keep installation IDs and four MCP tool names unchanged.
4. Update the GitHub About description, homepage URL, and relevant topics through `gh repo edit` after the refreshed article is live.
5. Run the focused release metadata test, full pytest suite, Ruff, and `scripts/sync_skill.py --check`.
6. Commit as `docs: turn README into an evidence-backed landing page`.

### Task 4: Update the launch article and add three scenario articles

**Files in `/Users/wangpeng/.config/superpowers/worktrees/Hexo_Blog_Source/academic-search-growth-content`:**
- Modify: `source/_posts/academic-paper-search-reproducible-literature-search.md`
- Create: `source/_posts/academic-search-topic-scoping-workflow.md`
- Create: `source/_posts/academic-search-hallucinated-citation-check.md`
- Create: `source/_posts/pubmed-mesh-search-workflow.md`
- Create: `source/images/posts/academic-paper-search/*.png`
- Modify: `tests/skill-launch-posts.test.cjs`

**Steps:**

1. Add failing article-contract tests for v0.2.0, seven-source boundaries, one copyable prompt per article, exact repository links, and local real-result images.
2. Run `npm test` after generation and confirm the new tests fail for missing/stale content.
3. Update the launch article and write the three scenario posts with distinct search intent, factual result summaries, limitations, and canonical links.
4. Copy the verified screenshot assets into the blog source and use descriptive alt text.
5. Run `npm run build:prod` and `npm test`.
6. Commit as `content: publish academic search scenario series`.

### Task 5: Perform blog visual and runtime QA

**Files:**
- No production files unless QA identifies a scoped defect.

**Steps:**

1. Start the local Hexo server on a free port.
2. Capture desktop and mobile screenshots for the updated launch article and all three new articles.
3. Verify article headers, code blocks, images, related posts, footer tags, Pjax, comments, no horizontal overflow, and no overlap.
4. If a defect is found, add a failing regression check where practical, apply the smallest scoped fix, regenerate, and repeat QA.
5. Record the tested URLs and viewport sizes in the final task evidence.

### Task 6: Publish the canonical surfaces

**Files:**
- Merge the two feature branches into their respective local `main` branches.

**Steps:**

1. Run fresh verification in both worktrees.
2. Push both feature branches, merge into `main`, and push `main` for each repository.
3. Wait for the blog deployment workflow and verify all four live article URLs.
4. Update the Academic Paper Search GitHub About description and homepage to the refreshed canonical article.
5. Confirm the public README and GitHub metadata reflect the merged commit.

### Task 7: Submit to academic and Agent Skills catalogs

**Targets:**
- `cosen1024/awesome-academic-skills`
- `cocoafun/awesome-academic-skills`
- `ai4s-research/awesome-ai-for-science`
- `modelscope/Awesome-Vibe-Research`
- `MinhaoXiong/awesome-automated-research`
- `VoltAgent/awesome-agent-skills`
- `O0000-code/awesome-academic-skills` as a human-review packet only because its policy forbids agent-filed submissions

**Steps:**

1. Read each target's current contribution guide and verify Academic Paper Search meets its inclusion boundary.
2. For each eligible target, fork, create one target-specific branch, edit the target's source-of-truth file, run its validation, push, and open a concise PR disclosing self-submission.
3. Do not open an automated submission where target policy requires a human nomination; prepare the exact form values and direct submission URL instead.
4. Record every PR, issue, skip reason, and prepared packet in `docs/community-submissions.md`.

### Task 8: Submit to MCP catalogs and registries

**Targets:**
- `punkpeye/awesome-mcp-servers`
- `appcypher/awesome-mcp-servers`
- `wong2/awesome-mcp-servers`
- `TensorBlock/awesome-mcp-servers`
- `in-fun/mcpbar`

**Steps:**

1. Validate current submission policies, schemas, transport/package requirements, and whether stdio plus `uvx` is accepted.
2. Submit only to catalogs whose runtime contract matches the existing package; do not claim hosted HTTP, Docker, npm, or unsupported clients.
3. Use target-specific descriptions emphasizing reproducible multi-source metadata search, provenance, identifier verification, and Codex/Claude Code compatibility.
4. Run repository validators where available and open the permitted PR or issue.
5. Use an eligible fallback catalog if a target no longer accepts submissions or requires unsupported packaging, until 8-12 qualified submissions or prepared human-only packets are recorded.
6. Update `docs/community-submissions.md` with URLs and status.

### Task 9: Close the measurement loop

**Files:**
- Modify: `docs/community-growth.md`
- Modify: `docs/community-submissions.md`

**Steps:**

1. Re-run the exact GitHub code-search baseline and exclude `wp-a/*`, automated package mirrors, and forks from the qualified-mention count.
2. Record submitted, open, merged, declined, and human-action-required totals.
3. Verify all primary repository and blog tests again.
4. Commit the final ledger update, merge it into `main`, and push.
5. Report accepted/pending submission URLs, live article URLs, verification results, and the next measurement date.
