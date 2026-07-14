# Maintenance and Release Runbook

## Compatibility contract

- Support Python 3.10-3.13.
- Keep MCP Python SDK on `mcp>=1.27,<2` until a tested v2 migration is released.
- Preserve `search_papers`, `get_paper_by_id`, `get_citation`, and `lookup_mesh`.
- Keep `pyproject.toml`, plugin manifests, marketplace metadata, and `.mcp.json`
  on the same semantic version.

## Pull request gates

Run from the repository root:

```bash
python -m pip install -e ".[test]"
python -m ruff check src tests
python -m pytest
python -m pytest mcp-server/tests
python -m build
twine check dist/*
claude plugin validate --strict plugins/nature-academic-search
```

Also run the Codex plugin validator from `plugin-creator` and the skill validator
from `skill-creator` when either manifest or `SKILL.md` changes.

## Trusted Publisher setup

PyPI and TestPyPI each require a one-time Trusted Publisher mapping:

- owner: `wp-a`
- repository: `nature-academic-search`
- workflow: `publish.yml`
- environment: `pypi` for PyPI or `testpypi` for TestPyPI

The workflow uses GitHub OIDC and must not contain a PyPI API token. Create the
matching protected GitHub environments before publishing.

## Release checklist

For the initial release, replace `v0.1.0` with the intended version in later
releases.

1. Confirm the package name is still available and no unexpected release exists.
2. Update versions in `pyproject.toml`, both plugin manifests, both marketplace
   files, and the plugin `.mcp.json` pin.
3. Run every pull request gate and explicit network smoke test.
4. Trigger `publish.yml` with `testpypi`; install the uploaded wheel in a clean
   environment and verify all four MCP tools.
5. Create tag and GitHub release `v0.1.0`. Publishing the release triggers the
   production PyPI environment.
6. Install from public PyPI, run `nature-academic-search preflight`, and validate
   both plugin marketplaces from the tag.
7. Record incompatibilities or release-specific migration notes in the GitHub
   release body rather than adding a changelog file to the skill.

## Routine maintenance

- Review monthly Dependabot updates for Python and GitHub Actions.
- Investigate scheduled network-smoke failures by source before changing retry
  behavior.
- Add regression tests before changing parsing, deduplication, or client install
  commands.
- Test MCP SDK v2 in a separate branch; do not relax the `<2` bound without a
  protocol and client compatibility release.
