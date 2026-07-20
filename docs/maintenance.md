# Maintenance and Release Runbook

## Compatibility contract

- Support Python 3.10-3.13.
- Keep MCP Python SDK on `mcp>=1.27,<2` until a tested v2 migration is released.
- Preserve `search_papers`, `get_paper_by_id`, `get_citation`, and `lookup_mesh`.
- Preserve publication/trial entity separation and explicit Semantic Scholar
  enrichment semantics.
- Keep `pyproject.toml`, plugin manifests, versioned marketplace metadata, and
  `.mcp.json` on the same semantic version.

## Pull request gates

Run from the repository root:

```bash
python -m pip install -e ".[test]"
python scripts/sync_skill.py --check
python -m ruff check src tests
python -m pytest
python -m pytest mcp-server/tests
python -m build
twine check dist/*
claude plugin validate --strict plugins/nature-academic-search
```

Also run the Codex plugin validator from `plugin-creator` and the skill validator
from `skill-creator` when either manifest or `SKILL.md` changes.

The canonical skill is `SKILL.md`. After changing it or its packaged references,
run `python scripts/sync_skill.py`, then rerun `--check`; do not hand-maintain a
different Claude/Codex plugin copy.

## Trusted Publisher setup

PyPI and TestPyPI each require a one-time Trusted Publisher mapping:

- owner: `wp-a`
- repository: `nature-academic-search`
- workflow: `publish.yml`
- environment: `pypi` for PyPI or `testpypi` for TestPyPI

The workflow uses GitHub OIDC and must not contain a PyPI API token. Create the
matching protected GitHub environments before publishing.

## Distribution policy

PyPI is a low-maintenance runtime distribution for the pinned `uvx` plugin
command. Publish only when code, fixes, embedded skill behavior, or required
metadata changes. Do not create a second package for the display brand.

## Release checklist

Choose the intended semantic version before starting and use it consistently:

```bash
VERSION=x.y.z
```

1. Confirm the package name is still available and no unexpected release exists.
2. Update versions in `pyproject.toml`, `src/nature_academic_search/__init__.py`,
   both plugin manifests, Claude marketplace metadata, tests, and the plugin
   `.mcp.json` pin. The Codex marketplace has no version field.
3. Run every pull request gate and explicit network smoke test.
4. If the TestPyPI Trusted Publisher is configured, trigger `publish.yml` with
   `testpypi`; install the uploaded wheel in a clean environment and verify all
   four MCP tools. Otherwise record the skip and require a clean local wheel
   install plus a successful pull-request build before production publishing.
5. Create tag and GitHub release `v${VERSION}`. Publishing the release triggers
   the production PyPI environment.
6. Install from public PyPI, run `nature-academic-search preflight`, and validate
   both plugin marketplaces from the tag.
7. Record incompatibilities or release-specific migration notes in the GitHub
   release body rather than adding a changelog file to the skill.

## Routine maintenance

- Review monthly Dependabot updates for Python and GitHub Actions.
- Investigate scheduled network-smoke failures by source before changing retry
  behavior.
- Keep the scheduled smoke workflow separate from push/PR CI. It should make at
  most one bounded request per source, skip Semantic Scholar when its secret is
  absent, and never print credential values.
- Add regression tests before changing parsing, deduplication, or client install
  commands.
- Test MCP SDK v2 in a separate branch; do not relax the `<2` bound without a
  protocol and client compatibility release.
