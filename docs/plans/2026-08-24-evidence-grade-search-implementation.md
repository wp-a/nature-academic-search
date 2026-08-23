# Evidence-Grade Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add reproducible search-run manifests, stable record IDs, and optional field-level citation verification while preserving existing MCP calls.

**Architecture:** Introduce a small provenance module for canonical IDs, run fingerprints, UTC timestamps, and secret-free manifests. The search coordinator adds additive `record_id` and `search_run` fields. A verification module compares caller-provided expected metadata against an identifier lookup; `get_paper_by_id` exposes it through an optional `expected` parameter and keeps the old response unchanged when omitted.

**Tech Stack:** Python 3.10+, MCP Python SDK v1, pytest, hashlib, uuid, datetime, JSON

---

### Task 1: Define stable provenance helpers

**Files:**
- Create: `src/nature_academic_search/provenance.py`
- Create: `tests/test_provenance.py`

**Step 1: Write failing tests**

Cover these behaviors:

```python
def test_strong_identifier_record_id_is_canonical() -> None:
    record = {"entity_type": "publication", "doi": "https://doi.org/10.1000/ABC."}
    assert stable_record_id(record) == "publication:doi:10.1000/abc"


def test_fallback_record_id_is_stable_across_mapping_order() -> None:
    first = {"title": "A Study", "year": 2024, "authors": ["Jane Doe"]}
    second = {"authors": ["Jane Doe"], "year": "2024", "title": "A study"}
    assert stable_record_id(first) == stable_record_id(second)


def test_fingerprint_depends_on_ordered_record_ids() -> None:
    assert result_fingerprint(["publication:doi:10.1/a"]) != result_fingerprint(
        ["publication:doi:10.1/b"]
    )
```

Use public helper names `stable_record_id` and `result_fingerprint` in the test.

**Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=src python -m pytest -q tests/test_provenance.py
```

Expected: collection fails because `nature_academic_search.provenance` does not
exist yet.

**Step 3: Implement minimal helpers**

Implement canonical DOI/PMID/PMCID/arXiv/OpenAlex/Semantic Scholar/NCT
namespaces. For records without a strong identifier, hash only normalized
entity type, title, year, and first author; return a short `sha256:` suffix.
Use `hashlib.sha256` and never include raw API credentials or URLs in the
fallback payload.

**Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=src python -m pytest -q tests/test_provenance.py
```

Expected: all provenance tests pass.

**Step 5: Commit**

```bash
git add src/nature_academic_search/provenance.py tests/test_provenance.py
git commit -m "feat: add stable research record provenance"
```

### Task 2: Add run manifests and record IDs to search output

**Files:**
- Modify: `src/nature_academic_search/search.py`
- Modify: `tests/test_search.py`

**Step 1: Write failing tests**

Add tests that assert:

- every final record has `record_id`;
- repeated searches with the same mocked records produce the same record IDs;
- the result contains `search_run.schema_version == "1"`;
- `search_run` includes query, entity type, requested sources, enrichers, UTC
  timestamps, raw/unique counts, and a `sha256:` result fingerprint;
- the manifest does not include strings from a fake API key or request header;
- existing `sources_queried`, `sources_succeeded`, `sources_skipped`, and
  `errors` remain unchanged.

**Step 2: Run targeted tests to verify they fail**

```bash
PYTHONPATH=src python -m pytest -q tests/test_search.py -k "record_id or search_run"
```

Expected: failures for missing `record_id` and `search_run`.

**Step 3: Implement minimal search integration**

In `search_all`, capture UTC start/end times and a UUID. After deduplication and
enrichment, assign stable IDs to finalized records and calculate the ordered
fingerprint. Add only the new `search_run` key and per-record `record_id`; do
not change existing result ordering or error semantics.

**Step 4: Run targeted tests to verify they pass**

```bash
PYTHONPATH=src python -m pytest -q tests/test_search.py -k "record_id or search_run"
```

Expected: all new search provenance tests pass.

**Step 5: Commit**

```bash
git add src/nature_academic_search/search.py tests/test_search.py
git commit -m "feat: add reproducible search run manifests"
```

### Task 3: Implement field-level metadata verification

**Files:**
- Create: `src/nature_academic_search/verification.py`
- Create: `tests/test_verification.py`

**Step 1: Write failing tests**

Cover:

```python
def test_matching_title_author_year_and_doi_is_verified() -> None: ...
def test_conflicting_year_reports_mismatch_without_overwriting_actual() -> None: ...
def test_missing_expected_metadata_is_manual_needed() -> None: ...
def test_trial_expected_fields_use_nct_status_not_paper_journal() -> None: ...
```

The comparison must normalize DOI wrappers, case, punctuation, whitespace, and
year strings. Author comparison must tolerate a caller providing only the first
author. The returned object includes `status`, per-field statuses, and a
`method` value; it must never mutate the actual record.

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src python -m pytest -q tests/test_verification.py
```

Expected: collection fails because the verification module does not exist.

**Step 3: Implement minimal comparison logic**

Implement `verify_record(expected, actual)` with the four public statuses:
`verified`, `mismatch`, `not_found`, and `manual_needed`. Use publication fields
title, authors, year, journal, and identifiers; use trial fields such as NCT ID,
title, status, sponsor, and dates when `entity_type == "trial"`.

**Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=src python -m pytest -q tests/test_verification.py
```

Expected: all verification helper tests pass.

**Step 5: Commit**

```bash
git add src/nature_academic_search/verification.py tests/test_verification.py
git commit -m "feat: add field-level citation verification"
```

### Task 4: Expose verification through the existing MCP tool

**Files:**
- Modify: `src/nature_academic_search/server.py`
- Modify: `tests/test_server.py`

**Step 1: Write failing tests**

Add tests that call:

```python
server.get_paper_by_id(
    "10.1000/example",
    expected={"title": "Expected title", "year": 2024, "doi": "10.1000/example"},
)
```

Assert that the response includes `verification`, while a call without
`expected` remains byte-for-byte equivalent to the existing mocked response.
Also assert malformed `expected` values return a safe JSON error and that trial
lookups do not compare paper-only journal fields.

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src python -m pytest -q tests/test_server.py -k verification
```

Expected: failure because `get_paper_by_id` has no `expected` parameter or
verification output.

**Step 3: Implement additive MCP support**

Add `expected: dict[str, Any] | None = None` to `get_paper_by_id`. Validate it is
a mapping, perform the existing lookup, and attach verification only when it is
provided. Preserve the four existing tool names and all old arguments. Update
the docstring and avoid logging expected citation content or secrets.

**Step 4: Run targeted and compatibility tests**

```bash
PYTHONPATH=src python -m pytest -q tests/test_server.py -k "verification or identifier or default_search"
```

Expected: all targeted tests pass.

**Step 5: Commit**

```bash
git add src/nature_academic_search/server.py tests/test_server.py
git commit -m "feat: expose optional citation verification"
```

### Task 5: Update the Skill and documentation contract

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `references/search-workflows.md`
- Modify: `references/dedup-engine.md`
- Modify: `tests/test_plugin_artifacts.py`
- Modify: `tests/test_release_metadata.py`

**Step 1: Write failing documentation assertions**

Require the docs to mention `search_run`, `record_id`, `result_fingerprint`,
optional `expected`, field-level verification, and the four statuses without
claiming that search results are automatically verified.

**Step 2: Run documentation tests to verify they fail**

```bash
PYTHONPATH=src python -m pytest -q tests/test_plugin_artifacts.py tests/test_release_metadata.py -k "search or release or verification"
```

Expected: failures for the new contract terms.

**Step 3: Update docs**

Explain how to save the JSON response as a run artifact, how to pass expected
metadata to `get_paper_by_id`, and how to keep `mismatch` / `manual_needed`
records out of verified exports. Keep the relay integration in the staged design
document; do not add provider configuration to A's base search path.

**Step 4: Run documentation tests and sync check**

```bash
PYTHONPATH=src python -m pytest -q tests/test_plugin_artifacts.py tests/test_release_metadata.py -k "search or release or verification"
python scripts/sync_skill.py --check
```

Expected: documentation assertions pass and the packaged Skill mirror is
synchronized.

**Step 5: Commit**

```bash
git add SKILL.md README.md references/search-workflows.md references/dedup-engine.md tests/test_plugin_artifacts.py tests/test_release_metadata.py
git commit -m "docs: document evidence-grade search contract"
```

### Task 6: Full verification and integration

**Files:**
- No additional source files; inspect all staged changes.

**Step 1: Run the complete local suite**

```bash
PYTHONPATH=src python -m pytest -q
python -m ruff check src tests
python scripts/sync_skill.py --check
git diff --check
```

Expected: all tests pass, Ruff reports no findings, Skill synchronization is
clean, and the diff has no whitespace errors.

**Step 2: Review compatibility**

Check `tests/test_server.py` for the exact four-tool contract and confirm old
calls without `expected` still pass. Confirm `uv.lock` remains user-owned and
untracked.

**Step 3: Commit and push A**

```bash
git status --short
git push origin main
```

Wait for the GitHub CI matrix and build to finish before starting B. Record the
CI URL and outcome in the handoff. Do not add relay credentials or provider
configuration in this stage.
