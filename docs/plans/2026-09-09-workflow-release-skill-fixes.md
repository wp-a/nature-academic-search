# Workflow, release, and installed skill fixes

**Goal:** Complete the four improvements requested after the README audit: working
default verification, screening-aware exports, consistent package distribution,
and synchronized local skill instructions.

**Architecture:** Reuse the MCP identifier lookup in the default workflow runner;
retain injectable functions for offline tests. Export records only when their
verification status is allowed and, when screening is enabled, their decision is
`include`. Keep pending/excluded records in the existing audit files. Validate the
built wheel outside the source checkout before publication.

**Scope:** Python package, its tests and release gates, relevant documentation,
and installed copies of this skill. Preserve the existing untracked `uv.lock`.
The user authorized GitHub / PyPI publication after verification.

## 1. Default workflow verification

- Files: `src/nature_academic_search/workflow.py`, `tests/test_workflow.py`,
  `tests/test_cli.py`.
- First reproduce default-runner and CLI verification failures with source adapters
  stubbed at the network boundary.
- Add a lazy default lookup using the MCP resolver, preserving `not_found`,
  metadata mismatches, missing identifiers, and recoverable source errors.
- Run the regression tests and the workflow/CLI suites before task 2.

## 2. Screening-aware export

- Files: `src/nature_academic_search/workflow.py`, `tests/test_workflow.py`.
- First demonstrate that excluded/pending records currently leak into RIS.
- With a `screen` step require `include`; without it retain verification-only
  export. Missing providers and failures keep pending records out of RIS.
- Verify include/exclude/pending/missing/invalid decisions, mismatched citations,
  and the no-screen path. Record export counts in the report for clear feedback.

## 3. Package version and wheel validation

- Files: package/plugin release metadata, version tests, `.github/workflows/ci.yml`,
  `.github/workflows/publish.yml`, reusable wheel smoke check, maintenance docs.
- Prepare version `0.3.1`; keep plugin pins and package metadata consistent.
- Build a wheel, install it in a clean environment, run outside the checkout
  without `PYTHONPATH`, and verify CLI commands and the four MCP tools.
- Add the same smoke gate to CI and publication. Public PyPI availability must
  never be claimed before the release has actually been published and checked.

## 4. Canonical and installed skill synchronization

- Files: `SKILL.md`, canonical references, managed plugin mirrors, installation
  documentation and existing local copies of this skill.
- Correct workflow instructions to reflect tasks 1–2, including the no-model
  path. Synchronize plugin mirrors with `scripts/sync_skill.py`.
- Compare installed Codex/Claude copies with the canonical managed files; replace
  only this skill's managed files and verify hashes, links and advertised tools.
- Do not change unrelated client configuration or other skills.

## Final verification

Run the full Python/legacy suites, lint, skill mirror check, package build, twine,
plugin validation, clean wheel smoke, and a bounded live source workflow. Update
README and maintenance instructions to describe the resulting behavior.
