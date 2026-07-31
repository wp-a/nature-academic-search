# Academic Paper Search Community Discovery Growth Design

**Date:** 2026-07-31

## Objective

Move Academic Paper Search from repository-internal discovery to repeatable third-party discovery. The primary 30-day target is not another release: it is at least 8 qualified listing submissions, at least 4 accepted third-party listings, and a measurable increase in external referrals.

## Evidence

The repository has 51 stars. GitHub traffic for the latest 14-day window reports 384 unique visitors and 171 unique cloners. Roughly 33 stars arrived during the same period, so the repository already converts interested visitors reasonably well.

Discovery is the weak point:

- GitHub supplied 349 unique referrers, while Google supplied 4 and `wpironman.top` supplied 1.
- Exact GitHub code search found 14 references to the repository URL, but all except the automated PyPI mirror are inside `wp-a` repositories.
- The GitHub About description and the launch article still describe the old three-source release, while v0.2.0 supports five default publication sources, Semantic Scholar enrichment, and ClinicalTrials.gov trials.
- The README explains contracts well but does not show a real result image in the first decision path.

The comparable `openags/paper-search-mcp` repository is referenced by at least 100 external GitHub files and appears in several academic, MCP, and AI-for-science catalogs. This indicates that ecosystem placement, rather than another connector, is the highest-leverage next step.

## Product Surface

The repository landing path will lead with one honest promise: Chinese-first, reproducible literature search for Codex and Claude Code. The first screen will retain concise installation commands and add a real, dated result image. Three copyable cases will map to the most recognizable user jobs:

1. scope a thesis or proposal topic;
2. verify a possibly hallucinated citation;
3. build a PubMed MeSH query.

Every case must distinguish demonstrated output from illustrative prompts. Screenshots must be rendered from saved real outputs produced by the current code and must show the query date and source status.

## Content System

The existing launch article will be updated from v0.1.2 to v0.2.0 instead of publishing a second generic release post. Three focused Chinese articles will each solve one job, provide one copyable prompt, show one real output, explain the human-review boundary, and link to the canonical repository.

The posts will share a restrained editorial visual system and local assets. They will not claim systematic-review completeness, access to unconnected databases, or proof that a citation supports a scientific claim merely because its identifier resolves.

## Distribution

Submissions will target three layers:

- academic and AI-for-science catalogs;
- MCP catalogs and registries;
- cross-client Agent Skills catalogs.

Each submission will follow the target repository's own format and contribution policy. No bulk copy-paste descriptions will be used. Repositories that forbid agent-filed submissions will receive a prepared human-review packet rather than an automated issue or pull request. Targets that require unsupported packaging, hosted transport, Docker images, or unverifiable claims will be skipped and replaced with a relevant fallback.

## Measurement

The project will track four funnel stages:

| Metric | Baseline | 30-day target |
|---|---:|---:|
| Qualified submissions | 0 | 8-12 |
| Accepted third-party listings | 0 | >=4 |
| Qualified external GitHub mentions | 0 | >=6 |
| External unique referrers per 14 days | 6 known | >=30 |

Stars remain a trailing outcome, with 100 stars as a milestone rather than the operating metric. Release count is not a growth KPI.

## Verification

- Repository tests and release metadata checks pass.
- Saved result examples contain no placeholders and identify source/date boundaries.
- Blog tests and production generation pass.
- Desktop and mobile screenshots verify the updated launch post and each new article.
- Each external submission is recorded with target, method, URL, status, and target-specific description.
- GitHub About metadata matches v0.2.0 behavior and points to the refreshed article.

