# Community Discovery Metrics

Academic Paper Search measures whether independent researchers and ecosystem maintainers can discover and reuse the project. Stars remain a useful trailing signal. Release count is not a growth KPI.

## Baseline

Recorded on 2026-07-31 before the community discovery sprint.

| Metric | Baseline | 30-day target | How it is counted |
|---|---:|---:|---|
| Qualified submissions | 0 | 8-12 | A target-specific PR, issue, registry entry, or human-review packet that meets the target's current contribution policy |
| Qualified third-party listings | 0 | >=4 | Accepted catalog entries in repositories outside the `wp-a` account |
| Qualified external GitHub mentions | 0 | >=6 | Repository URL references outside `wp-a/*`, excluding forks and automated package-index mirrors |
| External unique referrers | 6 known in 14 days | >=30 in 14 days | GitHub traffic referrers excluding `github.com` |
| GitHub stars | 51 | 100 milestone | Trailing outcome, not the weekly operating metric |

The same 14-day traffic window reported 384 unique repository visitors and 171 unique cloners. About 33 stars arrived during the comparable period, so the first intervention focuses on qualified discovery rather than adding another data source.

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

Record catalog outcomes from [the submission ledger](community-submissions.md). Owners with repository traffic access can also collect the rolling GitHub referrer window:

```bash
gh api repos/wp-a/nature-academic-search/traffic/popular/referrers
```

## Decision Rules

- If README conversion remains healthy but external referrers stay flat, invest in accepted listings and task-specific tutorials.
- If external traffic rises but stars and clones do not, improve the first-screen demonstration and installation path.
- If users clone but cannot complete preflight, prioritize installation reliability before another promotion round.
- Do not publish a package release only to create activity. Release when runtime behavior or compatibility changes.
