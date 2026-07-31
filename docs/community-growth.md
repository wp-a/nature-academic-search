# Community Discovery Metrics

Academic Paper Search measures whether independent researchers and ecosystem maintainers can discover and reuse the project. Stars remain a useful trailing signal. Release count is not a growth KPI.

## Baseline

Recorded on 2026-07-31 before the community discovery sprint.

| Metric | Baseline | 30-day target | How it is counted |
|---|---:|---:|---|
| Qualified submissions | 0 | 4-6 high-authority targets | An open, permitted PR, issue, or registry request to a relevant repository with at least 100 GitHub stars, activity within 180 days, and no archived status |
| Prepared nominations | 0 | Only high-authority targets | A complete packet or branch for a target that passes the same quality gate; preparation does not count as submitted |
| Qualified third-party listings | 0 | >=4 | Accepted catalog entries in repositories outside the `wp-a` account |
| Qualified external GitHub mentions | 0 | >=6 | Repository URL references outside `wp-a/*`, excluding forks and automated package-index mirrors |
| External unique referrers | 6 known in 14 days | >=30 in 14 days | GitHub traffic referrers excluding `github.com`, `wpironman.top`, and other owner-controlled domains |
| GitHub stars | 51 | 100 milestone | Trailing outcome, not the weekly operating metric |

The same 14-day traffic window reported 384 unique repository visitors and 171 unique cloners. About 33 stars arrived during the comparable period, so the first intervention focuses on qualified discovery rather than adding another data source.

## Current Checkpoint

Recorded on 2026-07-31 after the first community-submission round.

| Metric | Current | Evidence |
|---|---:|---|
| Qualified submissions | 6 | Open PRs or issues across six independent ecosystem repositories that pass the quality gate |
| Prepared nominations | 2 | Two high-authority upstream-blocked PR branches; these do not count as submitted |
| Withdrawn submissions | 2 | Closed after their target repositories measured below 100 GitHub stars |
| Qualified third-party listings | 0 | No submitted entry is merged into a target default branch yet |
| Qualified external GitHub mentions | 0 | Current code search found only owner-controlled repositories and one automated package-index mirror |
| External unique referrers | 6 known in 14 days | Google 4, `github-cn.com` 1, and `chatgpt.com` 1; GitHub and WPIRONMAN traffic excluded |
| GitHub stars | 51 | Trailing outcome only |

The next decision is based on accepted high-authority listings and independent references, not on opening more pull requests or publishing another package version.

## Target Quality Gate

- Prefer repositories with at least 500 GitHub stars.
- Consider repositories with 100-499 stars only when their audience directly matches academic research, Agent Skills, MCP, or AI for Science.
- Skip repositories below 100 stars, even when their submission process is easy.
- Require activity within the previous 180 days and reject archived repositories.
- Recheck stars and activity immediately before submission because both can change.

## Monthly Check

Next review: **2026-08-30**.

List exact repository references:

```bash
gh search code 'wp-a/nature-academic-search' \
  --limit 100 \
  --json repository,path,url
```

Review the results manually and exclude:

- any repository owned by `wp-a`;
- forks that merely copy the original README;
- generated PyPI/package-index mirrors;
- temporary submission branches that were never merged.

Prepared nominations become qualified submissions only after the account owner
personally files them. Referrer reviews likewise exclude WPIRONMAN and other
domains controlled by the project owner so the metric represents third-party
discovery rather than self-generated traffic.

Record catalog outcomes from [the submission ledger](community-submissions.md). Owners with repository traffic access can also collect the rolling GitHub referrer window:

```bash
gh api repos/wp-a/nature-academic-search/traffic/popular/referrers
```

## Decision Rules

- Apply the target quality gate before preparing a fork, packet, PR, or issue.
- If README conversion remains healthy but external referrers stay flat, invest in accepted listings and task-specific tutorials.
- If external traffic rises but stars and clones do not, improve the first-screen demonstration and installation path.
- If users clone but cannot complete preflight, prioritize installation reliability before another promotion round.
- Do not publish a package release only to create activity. Release when runtime behavior or compatibility changes.
