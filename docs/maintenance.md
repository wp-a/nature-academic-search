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

Run from the repository root with the uv version pinned in CI.

```bash
uv sync --locked --extra test
uv run --no-sync python scripts/sync_skill.py --check
uv run --no-sync python -m ruff check src tests scripts/check_wheel.py
uv run --no-sync python -m pytest
uv run --no-sync python -m pytest mcp-server/tests
uv run --no-sync python -m build
uv run --no-sync twine check dist/*
uv run --no-sync python scripts/check_wheel.py dist/*.whl
claude plugin validate --strict plugins/nature-academic-search
```

Run `uv lock` after changing package metadata or dependencies and commit
`uv.lock` alongside `pyproject.toml`. CI and publishing install the locked test
dependencies before running their checks.

Also run the Codex plugin validator from `plugin-creator` and the skill validator
from `skill-creator` when either manifest or `SKILL.md` changes.

The canonical skill is `SKILL.md`. After changing it or its packaged references,
run `python scripts/sync_skill.py`, then rerun `--check`; do not hand-maintain a
different Claude/Codex plugin copy.

The wheel checker accepts exactly one wheel and installs that artifact and its
dependencies into a temporary virtual environment. It checks dependencies and
runs outside the repository without `PYTHONPATH` or personal source/model
configuration. It checks the installed CLI version, `search`/`verify` commands
and JSON error behavior, packaged skill assets, and the four MCP tools through a
real stdio session. An offline workflow stubs only the Crossref request boundary
and must search, resolve, verify and export one record through the installed
runtime. Temporary files are removed when the check exits. Source connectivity
remains a separate network smoke gate.

Both CI and publishing must pass this installed-wheel check before uploading
build artifacts. Publishing also reruns the full package and legacy suites; a
release event must not bypass the tests used for pull requests.

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

The DeepSeek Harness integration lives in the standalone repository
[`wp-a/dsh-academic-paper-search`](https://github.com/wp-a/dsh-academic-paper-search).
Use the source installation documented there until the Bundle is available on
the public npm registry. It is a thin adapter over the PyPI MCP runtime and the official
`@deepseek-ai/dsh-mcp-client`; keep those contracts in sync:

- Update `cordis.patch.yml` in the standalone Bundle repository when the pinned
  `nature-academic-search==...` runtime changes.
- Keep the Bundle's dependency on the tested `@deepseek-ai/dsh-mcp-client`
  release; re-run the Bundle checks after upgrading DSH.
- Treat the Bundle version independently from the Python version. Bump it when
  its patch, install metadata, or compatibility documentation changes.
- Do not publish the Bundle from the Python release workflow until
  `npm pack --dry-run --json`, `node --check`, and a real DSH profile install
  have passed.

## Release checklist

Choose the intended semantic version before starting and use it consistently:

```bash
VERSION=x.y.z
```

1. Confirm the package name is still available and no unexpected release exists.
2. Update versions in `pyproject.toml`, `src/nature_academic_search/__init__.py`,
   both plugin manifests, Claude marketplace metadata, tests, and the plugin
   `.mcp.json` pin. Refresh `uv.lock` with `uv lock`. The Codex marketplace has no version field.
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

For a Bundle-only release, run the npm checks from the standalone repository,
publish the package from its root, and record the supported PyPI pin and DSH
version in the release notes.

## Routine maintenance

- Every release must install the built wheel into a clean temporary environment
  and invoke the actual CLI and MCP stdio entry points outside the source checkout.
  `scripts/check_wheel.py` performs this gate in CI and before publishing; metadata
  checks and editable-source tests alone do not prove the distributed commands work.
- Workflow `verify` uses the default identifier resolver. With a `screen` step,
  export requires both an allowed verification status and `include`; missing,
  invalid, pending or excluded decisions stay out of RIS. Without `screen`, export
  uses verification alone. Trial registrations remain in JSON. Preserve these
  behaviors in regressions and the bundled skill; include `exported_count` in reports.
- A workflow with a successful search can complete with zero hits. If some sources
  fail, it returns `completed_with_errors` and keeps the results from successful sources.
  If all sources fail, it returns `failed`, the CLI exits with code 1, and the run
  saves diagnostics without writing a new RIS. Use the run manifest to identify
  artifacts produced by the current run when reusing an output directory.
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
