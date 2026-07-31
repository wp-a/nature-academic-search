# Community Submission Ledger

This ledger records target-specific discovery work. It separates submissions from accepted listings so that project growth is measured by independent references rather than by the number of outbound pull requests.

## Status Vocabulary

- `planned`: target appears relevant but its current policy still needs verification.
- `prepared`: the target-specific packet is complete, but no permitted submission is open yet.
- `submitted`: a permitted PR, issue, or registry request is open.
- `accepted`: the project is visible in the target's default branch or public registry.
- `declined`: a maintainer declined the entry.
- `human action required`: the target explicitly prohibits agent-filed submissions or requires an interactive account-owner step.
- `skipped`: the target requires an unsupported runtime, packaging format, or claim.

## Academic and AI-for-science

| Target | Method | Status | submission_url | Notes |
|---|---|---|---|---|
| `cosen1024/awesome-academic-skills` | Data PR | skipped | - | Its validator requires every entry date to equal the catalog-wide verification date; adding a current entry would require falsely redating or re-verifying all 39 existing entries. |
| `cocoafun/awesome-academic-skills` | PR | submitted | https://github.com/cocoafun/awesome-academic-skills/pull/2 | One factual entry in Literature Review & Paper Discovery. |
| `ai4s-research/awesome-ai-for-science` | PR | submitted | https://github.com/ai4s-research/awesome-ai-for-science/pull/86 | One entry in Literature & Knowledge Management. |
| `modelscope/Awesome-Vibe-Research` | PR | submitted | https://github.com/modelscope/Awesome-Vibe-Research/pull/17 | Includes the dated Chinese topic-scoping result as the practice link. |
| `MinhaoXiong/awesome-automated-research` | PR | submitted | https://github.com/MinhaoXiong/awesome-automated-research/pull/7 | English and Chinese literature-tool rows. |
| `O0000-code/awesome-academic-skills` | Issue form packet | prepared | [human submission packet](community-submission-packets/o0000-code-awesome-academic-skills.md) | Human action required: contribution policy requires the recommendation itself to be submitted by a human. |

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
| `in-fun/mcpbar` | Manifest PR | submitted | https://github.com/in-fun/mcpbar/pull/5 | Manifest pins package `0.2.0`; JSON parse and published `uvx` entrypoint checks passed. |

## Current Checkpoint

Recorded on 2026-07-31 after the first submission round.

| Metric | Current | Counting note |
|---|---:|---|
| Qualified submissions | 8 | Eight independent targets have an open, permitted PR or issue. |
| Prepared submissions | 3 | One human-only packet and two compare branches; none count as submitted. |
| Qualified third-party listings | 0 | Open submissions become listings only after merge or registry publication. |

## Submission Copy Principles

- Disclose that the submitter maintains Academic Paper Search.
- Describe the verified behavior in the target's own taxonomy.
- Do not claim Google Scholar, Web of Science, Scopus, Embase, CNKI, hosted HTTP, Docker, or npm support.
- Keep publication search separate from ClinicalTrials.gov trial records.
- Link to a dated real-result example when the target permits supporting links.
