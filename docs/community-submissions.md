# Community Submission Ledger

This ledger records target-specific discovery work. It separates submissions from accepted listings so that project growth is measured by independent references rather than by the number of outbound pull requests.

## Status Vocabulary

- `planned`: target appears relevant but its current policy still needs verification.
- `prepared`: the target-specific packet is complete, but no permitted submission is open yet.
- `submitted`: a permitted PR, issue, or registry request is open.
- `accepted`: the project is visible in the target's default branch or public registry.
- `declined`: a maintainer declined the entry.
- `withdrawn`: the submitter closed an open request because it no longer passes the project quality gate.
- `human action required`: the target explicitly prohibits agent-filed submissions or requires an interactive account-owner step.
- `skipped`: the target requires an unsupported runtime, packaging format, or claim.

## Target Quality Gate

- Prefer targets with at least 500 GitHub stars.
- Submit to targets with 100-499 stars only when their audience is an exact fit.
- Skip targets below 100 stars.
- Require a non-archived repository with activity in the previous 180 days.

## Academic and AI-for-science

| Target | Method | Status | submission_url | Notes |
|---|---|---|---|---|
| `cosen1024/awesome-academic-skills` | Data PR | skipped | - | 6 stars at review time; also has a catalog-wide date invariant that prevents an honest minimal entry. |
| `cocoafun/awesome-academic-skills` | PR | withdrawn | https://github.com/cocoafun/awesome-academic-skills/pull/2 | Closed by the submitter after the target measured 1 star, below the 100-star floor. |
| `ai4s-research/awesome-ai-for-science` | PR | submitted | https://github.com/ai4s-research/awesome-ai-for-science/pull/86 | One entry in Literature & Knowledge Management. |
| `modelscope/Awesome-Vibe-Research` | PR | submitted | https://github.com/modelscope/Awesome-Vibe-Research/pull/17 | Includes the dated Chinese topic-scoping result as the practice link. |
| `MinhaoXiong/awesome-automated-research` | PR | submitted | https://github.com/MinhaoXiong/awesome-automated-research/pull/7 | English and Chinese literature-tool rows. |
| `O0000-code/awesome-academic-skills` | Issue form | skipped | - | 14 stars at review time, below the 100-star floor; its human-only submission policy is therefore no longer relevant. |

## Agent Skills

| Target | Method | Status | submission_url | Notes |
|---|---|---|---|---|
| `VoltAgent/awesome-agent-skills` | PR | submitted | https://github.com/VoltAgent/awesome-agent-skills/pull/860 | Community Skills / Specialized Domains; description kept within 10 words. |

## MCP catalogs and registries

| Target | Method | Status | submission_url | Notes |
|---|---|---|---|---|
| `punkpeye/awesome-mcp-servers` | PR | submitted | https://github.com/punkpeye/awesome-mcp-servers/pull/11253 | Agent opt-in title used and repository check passed; acceptance still requires a signed-in Glama listing and score badge. |
| `appcypher/awesome-mcp-servers` | PR branch | prepared | https://github.com/appcypher/awesome-mcp-servers/compare/main...wp-a:add-nature-academic-search | Upstream has Issues disabled and GitHub denied `CreatePullRequest`; the compare branch is not counted as submitted. |
| `wong2/awesome-mcp-servers` | PR branch | prepared | https://github.com/wong2/awesome-mcp-servers/compare/main...wp-a:add-nature-academic-search | Upstream has Issues disabled and GitHub denied `CreatePullRequest`; the compare branch is not counted as submitted. |
| `TensorBlock/awesome-mcp-servers` | Issue form | submitted | https://github.com/TensorBlock/awesome-mcp-servers/issues/1491 | Intake automation opened review PR [#1492](https://github.com/TensorBlock/awesome-mcp-servers/pull/1492); the target counts once. |
| `in-fun/mcpbar` | Manifest PR | withdrawn | https://github.com/in-fun/mcpbar/pull/5 | Closed by the submitter after the target measured 21 stars, below the 100-star floor. |

## Current Checkpoint

Recorded on 2026-07-31 after the first submission round.

| Metric | Current | Counting note |
|---|---:|---|
| Qualified submissions | 6 | Six independent high-authority targets have an open, permitted PR or issue. |
| Prepared submissions | 2 | Two high-authority compare branches; neither counts as submitted. |
| Withdrawn submissions | 2 | Two low-authority requests were closed after the quality gate was adopted. |
| Qualified third-party listings | 0 | Open submissions become listings only after merge or registry publication. |

## Submission Copy Principles

- Disclose that the submitter maintains Academic Paper Search.
- Describe the verified behavior in the target's own taxonomy.
- Do not claim Google Scholar, Web of Science, Scopus, Embase, CNKI, hosted HTTP, Docker, or npm support.
- Keep publication search separate from ClinicalTrials.gov trial records.
- Link to a dated real-result example when the target permits supporting links.
