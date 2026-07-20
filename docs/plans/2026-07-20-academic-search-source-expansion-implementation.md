# Academic Paper Search Source Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add OpenAlex and Europe PMC as default publication sources, Semantic Scholar as explicit search/enrichment, and ClinicalTrials.gov as a separately modelled trial source while preserving all existing MCP contracts.

**Architecture:** Introduce a capability-aware source registry and a shared secret-safe JSON request helper for the four new APIs. Keep publication and trial records separate, extend deduplication with source-specific identifiers and metric provenance, and route new behavior through the existing four MCP tools without breaking old calls.

**Tech Stack:** Python 3.10-3.13, `requests`, `asyncio`, FastMCP, pytest, Ruff, Hatch/build, Codex and Claude Code plugin manifests.

---

## Preconditions

- Work in an isolated worktree based on `main`.
- Read `docs/plans/2026-07-20-academic-search-source-expansion-design.md` completely.
- Use @test-driven-development for every behavior change.
- Use @systematic-debugging for unexpected test or live-API failures.
- Use @writing-skills before editing canonical or packaged `SKILL.md`.
- Use @verification-before-completion before each merge or release claim.
- Do not modify, delete, or commit the user's untracked `uv.lock` in the main
  worktree.
- Do not tag, publish to PyPI, create a GitHub release, or change repository
  metadata without separate user approval.
- Use official API documentation as the source of truth. The local `chub`
  command was unavailable during design; retry it before implementation and
  fall back to the official links recorded in the design if it remains absent.

## Task 1: Freeze Compatibility and Source Contracts

**Files:**

- Create: `tests/test_source_registry.py`
- Create: `tests/fixtures/sources/openalex-search.json`
- Create: `tests/fixtures/sources/europe-pmc-search.json`
- Create: `tests/fixtures/sources/semantic-scholar-search.json`
- Create: `tests/fixtures/sources/clinicaltrials-search.json`
- Modify: `tests/test_server.py`
- Modify: `tests/test_search.py`

### Step 1: Add sanitized source fixtures

Create minimal fixtures from official response schemas. Keep only fields the
normalizers need and use fictional titles/authors. Every fixture must include a
source-native ID and at least one cross-source identifier where supported.

Example OpenAlex fixture shape:

```json
{
  "meta": {"count": 1, "cost_usd": 0.001},
  "results": [
    {
      "id": "https://openalex.org/W1234567890",
      "doi": "https://doi.org/10.1000/example",
      "display_name": "Example study",
      "publication_year": 2025,
      "publication_date": "2025-02-03",
      "cited_by_count": 7,
      "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/12345678"},
      "authorships": [{"author": {"display_name": "Researcher One"}}]
    }
  ]
}
```

Do not copy real abstracts or large third-party payloads.

### Step 2: Write failing registry and compatibility tests

Add tests specifying canonical source sets and the unchanged MCP tool names:

```python
def test_source_sets_are_entity_specific() -> None:
    from nature_academic_search.sources.registry import (
        DEFAULT_PUBLICATION_SOURCES,
        OPTIONAL_PUBLICATION_SOURCES,
        TRIAL_SOURCES,
    )

    assert DEFAULT_PUBLICATION_SOURCES == (
        "crossref",
        "pubmed",
        "arxiv",
        "openalex",
        "europe_pmc",
    )
    assert OPTIONAL_PUBLICATION_SOURCES == ("semantic_scholar",)
    assert TRIAL_SOURCES == ("clinicaltrials_gov",)
```

Keep the existing assertion that the server exposes exactly:

```python
{"search_papers", "get_paper_by_id", "get_citation", "lookup_mesh"}
```

Add a legacy call test confirming an explicit three-source request still reaches
only `crossref`, `pubmed`, and `arxiv`.

### Step 3: Run the tests and verify RED

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_source_registry.py \
  tests/test_server.py \
  tests/test_search.py -v
```

Expected: FAIL because `sources.registry` and the new source contracts do not
exist. Existing compatibility tests should remain green.

### Step 4: Add the minimal registry constants

Create `src/nature_academic_search/sources/registry.py` with the three source
tuples and a mapping from source name to entity type. Do not instantiate adapters
yet.

### Step 5: Run focused tests

Run the same command. Expected: the registry tests pass; fixture-driven adapter
tests remain pending for later tasks.

### Step 6: Commit

```bash
git add tests/test_source_registry.py tests/fixtures/sources \
  tests/test_server.py tests/test_search.py \
  src/nature_academic_search/sources/registry.py
git commit -m "test: define expanded academic source contracts"
```

## Task 2: Add Configuration and a Secret-Safe Request Helper

**Files:**

- Create: `src/nature_academic_search/http.py`
- Create: `tests/test_http.py`
- Modify: `src/nature_academic_search/config.py`
- Modify: `tests/test_package_metadata.py`

### Step 1: Write failing configuration tests

Use `monkeypatch` to define environment values and instantiate `Config` directly:

```python
def test_new_source_configuration_is_environment_driven(monkeypatch) -> None:
    monkeypatch.setenv("OPENALEX_API_KEY", "openalex-test")
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "s2-test")
    monkeypatch.setenv("EUROPE_PMC_TIMEOUT", "17")
    monkeypatch.setenv("CLINICALTRIALS_GOV_TIMEOUT", "19")

    config = Config()

    assert config.openalex_api_key == "openalex-test"
    assert config.semantic_scholar_api_key == "s2-test"
    assert config.europe_pmc_timeout == 17
    assert config.clinicaltrials_gov_timeout == 19
```

Also test TOML fallbacks and invalid timeout values.

### Step 2: Write failing HTTP behavior tests

Mock `requests.Session.request` and specify:

- successful JSON decode;
- timeout converted to `DataSourceError`;
- bounded retries for `429`, `502`, `503`, and `504`;
- numeric `Retry-After` honored with a bounded sleep;
- no retry for `400` or `404`;
- API key and authorization values absent from exception text;
- malformed JSON converted to `DataSourceError`;
- selected rate-limit headers returned separately from the payload.

Example redaction assertion:

```python
with pytest.raises(DataSourceError) as error:
    request_json(
        source="semantic_scholar",
        method="GET",
        url="https://example.test",
        headers={"x-api-key": "super-secret"},
    )

assert "super-secret" not in str(error.value)
```

### Step 3: Verify RED

Run:

```bash
.venv/bin/python -m pytest tests/test_http.py tests/test_package_metadata.py -v
```

Expected: FAIL because the helper and properties do not exist.

### Step 4: Implement the minimal helper and configuration

Add configuration properties for:

- `OPENALEX_API_KEY`
- `OPENALEX_TIMEOUT`
- `SEMANTIC_SCHOLAR_API_KEY`
- `SEMANTIC_SCHOLAR_TIMEOUT`
- `EUROPE_PMC_TIMEOUT`
- `CLINICALTRIALS_GOV_TIMEOUT`

Implement `request_json` with at most two retries, bounded exponential backoff,
numeric `Retry-After`, explicit timeout, and credential redaction. Do not migrate
the three existing adapters in this task.

### Step 5: Verify GREEN and lint

```bash
.venv/bin/python -m pytest tests/test_http.py tests/test_package_metadata.py -v
.venv/bin/python -m ruff check src/nature_academic_search/http.py \
  src/nature_academic_search/config.py tests/test_http.py
```

### Step 6: Commit

```bash
git add src/nature_academic_search/http.py \
  src/nature_academic_search/config.py tests/test_http.py \
  tests/test_package_metadata.py
git commit -m "feat: add source request and configuration primitives"
```

## Task 3: Implement the OpenAlex Adapter

**Files:**

- Create: `src/nature_academic_search/sources/openalex.py`
- Create: `tests/test_source_openalex.py`
- Modify: `src/nature_academic_search/sources/__init__.py`
- Modify: `tests/test_sources.py`

### Step 1: Write failing fixture-driven tests

Test that `OpenAlexSource.search("example", rows=5)` sends:

```python
{
    "search": "example",
    "per_page": 5,
    "select": "...bounded field list...",
}
```

When configured, the request also sends `api_key` without logging it.

Assert normalized fields:

```python
assert record["entity_type"] == "publication"
assert record["source"] == "openalex"
assert record["source_id"] == "W1234567890"
assert record["openalex_id"] == "W1234567890"
assert record["doi"] == "10.1000/example"
assert record["pmid"] == "12345678"
assert record["citation_count"] == 7
assert record["citation_count_source"] == "openalex"
assert record["citation_counts"] == {"openalex": 7}
```

Test reconstruction of `abstract_inverted_index`, missing optional fields,
singleton lookup by OpenAlex ID/URL/DOI, and returned cost/rate metadata.

### Step 2: Verify RED

```bash
.venv/bin/python -m pytest tests/test_source_openalex.py tests/test_sources.py -v
```

Expected: FAIL because `OpenAlexSource` does not exist.

### Step 3: Implement the adapter

Use `/works` for search and singleton `/works/{id}` lookups. Request only the
fields required by the normalized model. Cap `rows` at the configured maximum;
never paginate automatically.

### Step 4: Verify GREEN and lint

```bash
.venv/bin/python -m pytest tests/test_source_openalex.py tests/test_sources.py -v
.venv/bin/python -m ruff check src/nature_academic_search/sources/openalex.py \
  tests/test_source_openalex.py
```

### Step 5: Commit

```bash
git add src/nature_academic_search/sources/openalex.py \
  src/nature_academic_search/sources/__init__.py \
  tests/test_source_openalex.py tests/test_sources.py
git commit -m "feat: add OpenAlex publication source"
```

## Task 4: Implement the Europe PMC Adapter

**Files:**

- Create: `src/nature_academic_search/sources/europe_pmc.py`
- Create: `tests/test_source_europe_pmc.py`
- Modify: `src/nature_academic_search/sources/__init__.py`
- Modify: `tests/test_sources.py`

### Step 1: Write failing adapter tests

Use the sanitized Europe PMC fixture and assert:

- query, page size, JSON format, and bounded result count;
- `entity_type="publication"`;
- normalized DOI, PMID, PMCID, year, authors, journal, and publication type;
- preprint and peer-review status are not conflated;
- open-full-text status and URL are source-attributed;
- lookups by PMID and PMCID;
- zero-result and malformed-record handling.

### Step 2: Verify RED

```bash
.venv/bin/python -m pytest tests/test_source_europe_pmc.py tests/test_sources.py -v
```

### Step 3: Implement the adapter

Use the Europe PMC REST search endpoint with JSON output. Normalize `id`,
`source`, `pmid`, `pmcid`, and `doi` defensively; do not infer peer review from
the presence of a title or abstract.

### Step 4: Verify GREEN and lint

```bash
.venv/bin/python -m pytest tests/test_source_europe_pmc.py tests/test_sources.py -v
.venv/bin/python -m ruff check src/nature_academic_search/sources/europe_pmc.py \
  tests/test_source_europe_pmc.py
```

### Step 5: Commit

```bash
git add src/nature_academic_search/sources/europe_pmc.py \
  src/nature_academic_search/sources/__init__.py \
  tests/test_source_europe_pmc.py tests/test_sources.py
git commit -m "feat: add Europe PMC publication source"
```

## Task 5: Extend Publication Routing, Deduplication, and Provenance

**Files:**

- Modify: `src/nature_academic_search/search.py`
- Modify: `src/nature_academic_search/sources/registry.py`
- Modify: `tests/test_search.py`
- Modify: `tests/test_source_registry.py`

### Step 1: Write failing default-routing tests

Inject fake adapters and assert an omitted source list attempts exactly:

```python
[
    "crossref",
    "pubmed",
    "arxiv",
    "openalex",
    "europe_pmc",
]
```

Assert explicit legacy source lists remain unchanged. Add response assertions for
`sources_queried`, `sources_succeeded`, `sources_skipped`, and structured
`errors`.

### Step 2: Write failing deduplication tests

Cover:

- PubMed + Europe PMC merge by PMID/PMCID/DOI;
- OpenAlex + CrossRef merge by DOI;
- OpenAlex + arXiv merge by arXiv ID;
- source records preserved in observed order;
- conflicting non-empty identifiers recorded instead of overwritten;
- citation counts retained per source;
- `citation_count_source` follows the representative compatibility value;
- `entity_type` included in every key.

### Step 3: Verify RED

```bash
.venv/bin/python -m pytest tests/test_search.py tests/test_source_registry.py -v
```

### Step 4: Replace source-specific branching with capabilities

Update the registry to construct adapters lazily and record capabilities such as
`search`, `lookup`, `type_filter`, and `enrich`. Update `_search_one` to consult
capabilities rather than comparing source names.

Extend `_prepare_record`, `_record_keys`, and `_merge_record` according to the
design. Preserve first-source ordering and existing fields.

### Step 5: Verify GREEN and full existing search regression

```bash
.venv/bin/python -m pytest tests/test_search.py tests/test_source_registry.py -v
.venv/bin/python -m pytest tests/test_server.py tests/test_sources.py -v
.venv/bin/python -m ruff check src tests
```

### Step 6: Commit

```bash
git add src/nature_academic_search/search.py \
  src/nature_academic_search/sources/registry.py \
  tests/test_search.py tests/test_source_registry.py
git commit -m "feat: route and merge five publication sources"
```

## Task 6: Implement Semantic Scholar Search and Enrichment

**Files:**

- Create: `src/nature_academic_search/sources/semantic_scholar.py`
- Create: `tests/test_source_semantic_scholar.py`
- Modify: `src/nature_academic_search/sources/__init__.py`
- Modify: `src/nature_academic_search/sources/registry.py`
- Modify: `src/nature_academic_search/search.py`
- Modify: `tests/test_search.py`

### Step 1: Write failing search tests

Assert the adapter:

- calls `/graph/v1/paper/search` only when explicitly selected;
- requests a bounded field list;
- sends `x-api-key` when configured and never emits it;
- applies a conservative local request interval;
- normalizes DOI, arXiv ID, S2 paper ID, authors, year, venue, abstract,
  citation count, reference count, and open-access PDF metadata.

### Step 2: Write failing enrichment tests

Specify strong-ID-only enrichment:

```python
result = await enrich_records(
    records,
    enrichers=["semantic_scholar"],
    adapters={"semantic_scholar": fake_s2},
)
```

Assert:

- at most the returned top `rows` records are looked up;
- DOI is preferred, then arXiv ID, then supported PMID;
- records without strong IDs are skipped, not keyword matched;
- lookup failures do not discard the publication;
- S2 citation counts are added under `citation_counts` with provenance;
- no recursive citation/reference traversal occurs.

### Step 3: Verify RED

```bash
.venv/bin/python -m pytest \
  tests/test_source_semantic_scholar.py tests/test_search.py -v
```

### Step 4: Implement adapter and enrichment stage

Add explicit search and singleton lookup methods. Add a bounded enrichment stage
after deduplication. Keep Semantic Scholar out of
`DEFAULT_PUBLICATION_SOURCES`.

### Step 5: Verify GREEN and lint

```bash
.venv/bin/python -m pytest \
  tests/test_source_semantic_scholar.py tests/test_search.py -v
.venv/bin/python -m ruff check src tests
```

### Step 6: Commit

```bash
git add src/nature_academic_search/sources/semantic_scholar.py \
  src/nature_academic_search/sources/__init__.py \
  src/nature_academic_search/sources/registry.py \
  src/nature_academic_search/search.py \
  tests/test_source_semantic_scholar.py tests/test_search.py
git commit -m "feat: add Semantic Scholar enrichment"
```

## Task 7: Implement ClinicalTrials.gov as a Trial Entity

**Files:**

- Create: `src/nature_academic_search/sources/clinicaltrials.py`
- Create: `tests/test_source_clinicaltrials.py`
- Modify: `src/nature_academic_search/sources/__init__.py`
- Modify: `src/nature_academic_search/sources/registry.py`
- Modify: `src/nature_academic_search/search.py`
- Modify: `tests/test_search.py`

### Step 1: Write failing adapter tests

Use the sanitized API v2 fixture and assert normalization of:

- NCT ID and study URL;
- official/brief title;
- study type and overall status;
- conditions and interventions;
- sponsor, enrollment, locations;
- start/completion/update dates;
- registry `dataTimestamp` when available;
- linked publication references without treating them as the trial itself.

Test lookup by `NCT01234567` and ClinicalTrials.gov study URL.

### Step 2: Write failing entity-isolation tests

Assert:

- `entity_type="trial"` defaults to `clinicaltrials_gov`;
- publication sources with `entity_type="trial"` are rejected;
- `clinicaltrials_gov` with `entity_type="publication"` is rejected;
- trial deduplication uses NCT ID only;
- identical publication/trial titles never merge;
- trial results do not receive paper citation fields by inference.

### Step 3: Verify RED

```bash
.venv/bin/python -m pytest \
  tests/test_source_clinicaltrials.py tests/test_search.py -v
```

### Step 4: Implement the trial adapter and route

Use `/api/v2/studies` for search and `/api/v2/studies/{nctId}` for singleton
lookup. Parse nested modules defensively and preserve null/missing fields without
inference.

### Step 5: Verify GREEN and lint

```bash
.venv/bin/python -m pytest \
  tests/test_source_clinicaltrials.py tests/test_search.py -v
.venv/bin/python -m ruff check src tests
```

### Step 6: Commit

```bash
git add src/nature_academic_search/sources/clinicaltrials.py \
  src/nature_academic_search/sources/__init__.py \
  src/nature_academic_search/sources/registry.py \
  src/nature_academic_search/search.py \
  tests/test_source_clinicaltrials.py tests/test_search.py
git commit -m "feat: add ClinicalTrials.gov trial search"
```

## Task 8: Extend the Stable MCP Tools and Identifier Routing

**Files:**

- Modify: `src/nature_academic_search/server.py`
- Modify: `mcp-server/academic_search_server.py`
- Modify: `tests/test_server.py`
- Modify: `mcp-server/tests/test_sources.py`

### Step 1: Write failing signature and routing tests

Test the existing tool list remains exactly four. Add tests for:

- `search_papers(..., entity_type="publication")` default routing;
- `search_papers(..., entity_type="trial")` trial routing;
- explicit `sources=["semantic_scholar"]`;
- `enrich=["semantic_scholar"]` passed after deduplication;
- invalid entity/source combinations rejected before adapter calls;
- PMCID, OpenAlex, NCT, and Semantic Scholar URL detection;
- explicit `id_type="semantic_scholar"` accepted;
- `get_paper_by_id` dispatch to the correct adapter;
- `get_citation` rejects NCT records with a structured, non-fabricated message;
- old DOI, PMID, and arXiv routes unchanged.

### Step 2: Verify RED

```bash
.venv/bin/python -m pytest tests/test_server.py mcp-server/tests/test_sources.py -v
```

### Step 3: Implement minimal server changes

Construct adapter instances through the registry. Extend `detect_id_type` and
`_resolve_id_type`. Keep compatibility imports in
`mcp-server/academic_search_server.py` synchronized.

For publication IDs that resolve to a DOI, continue to prefer CrossRef content
negotiation for formatted citations. For PMCID/OpenAlex/S2 records without a DOI,
use the existing basic citation fallback and label its metadata source.

### Step 4: Verify GREEN and the compatibility suite

```bash
.venv/bin/python -m pytest tests/test_server.py -v
.venv/bin/python -m pytest mcp-server/tests -v
.venv/bin/python -m ruff check src tests
```

### Step 5: Commit

```bash
git add src/nature_academic_search/server.py \
  mcp-server/academic_search_server.py \
  tests/test_server.py mcp-server/tests/test_sources.py
git commit -m "feat: extend MCP routing for publications and trials"
```

## Task 9: Extend Preflight and Scheduled Network Smoke Checks

**Files:**

- Modify: `src/nature_academic_search/preflight.py`
- Modify: `tests/test_cli.py`
- Modify: `.github/workflows/network-smoke.yml`
- Modify: `mcp-server/config.toml`
- Modify: `config/settings-snippet.json`
- Modify: `config/mcp-snippet.json`

### Step 1: Write failing preflight tests

Mock endpoint checks and assert reports for all seven sources. Ensure:

- optional API keys are reported as configured/missing without printing values;
- OpenAlex anonymous availability is represented separately from keyed budget;
- Semantic Scholar credentialed smoke is skipped when its secret is absent;
- ClinicalTrials.gov reports API/data version timestamp when available;
- source failure affects only that source's capability line.

### Step 2: Verify RED

```bash
.venv/bin/python -m pytest tests/test_cli.py -v
```

### Step 3: Implement preflight and workflow changes

Add low-cost endpoint checks. The scheduled workflow must:

- never run during ordinary push/PR CI;
- make one bounded query or singleton request per enabled source;
- skip secret-dependent checks when GitHub secrets are absent;
- avoid exact result-count assertions;
- never print credentials.

Update example config with empty optional key fields and timeouts. Do not put real
credentials in any snippet.

### Step 4: Verify GREEN

```bash
.venv/bin/python -m pytest tests/test_cli.py -v
.venv/bin/python -m ruff check src tests
git diff --check
```

### Step 5: Commit

```bash
git add src/nature_academic_search/preflight.py tests/test_cli.py \
  .github/workflows/network-smoke.yml mcp-server/config.toml \
  config/settings-snippet.json config/mcp-snippet.json
git commit -m "test: extend source preflight and network smoke"
```

## Task 10: Update the Canonical Skill, Plugin Mirror, and Documentation

**Files:**

- Modify: `SKILL.md`
- Modify: `plugins/nature-academic-search/skills/nature-academic-search/SKILL.md`
- Modify: `README.md`
- Modify: `mcp-server/README.md`
- Modify: `docs/installation.md`
- Modify: `docs/maintenance.md`
- Modify: `references/source-tiers.md`
- Modify: `references/search-workflows.md`
- Modify: `references/workflows/wf1-multi-source-search.md`
- Modify: `tests/test_plugin_artifacts.py`
- Modify: `tests/test_release_metadata.py`

### Step 1: Use @writing-skills and write failing documentation contracts

Add assertions for:

- all seven source names and their distinct roles;
- `entity_type=trial` and the trial/publication boundary;
- Semantic Scholar explicit enrichment;
- configured/queried/succeeded/skipped/failed source reporting;
- source-attributed citation counts;
- no claims of Google Scholar, Scopus, Web of Science, Embase, CNKI, or Wanfang
  access;
- unchanged Codex/Claude installation identifiers;
- canonical and packaged Skill mirror equality.

### Step 2: Verify RED

```bash
.venv/bin/python -m pytest \
  tests/test_plugin_artifacts.py tests/test_release_metadata.py -v
```

### Step 3: Update the canonical Skill and references

Keep `SKILL.md` concise. Route detailed source roles, filters, provenance, and
trial behavior to `references/source-tiers.md` and
`references/search-workflows.md`.

The Skill must explicitly state:

- OpenAlex and Europe PMC are default publication sources;
- Semantic Scholar is explicit/enrichment;
- ClinicalTrials.gov records are trial registrations, not papers;
- actual tool output, not adapter existence, proves a source was queried;
- partial failures and skipped sources must be disclosed.

### Step 4: Synchronize the packaged Skill

Copy the canonical Skill/references using the repository's established packaging
workflow. If no sync command exists, add a deterministic sync/check script with
tests rather than maintaining manual drift.

### Step 5: Verify GREEN, links, and validators

```bash
.venv/bin/python -m pytest \
  tests/test_plugin_artifacts.py tests/test_release_metadata.py -v
.venv/bin/python /Users/wangpeng/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
.venv/bin/python /Users/wangpeng/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/nature-academic-search
claude plugin validate --strict plugins/nature-academic-search
git diff --check
```

### Step 6: Commit

```bash
git add SKILL.md README.md mcp-server/README.md docs references \
  plugins/nature-academic-search/skills/nature-academic-search \
  tests/test_plugin_artifacts.py tests/test_release_metadata.py
git commit -m "docs: explain seven-source search routing"
```

## Task 11: Build, Review, and Verify the Complete Feature

**Files:**

- Modify only files required by accepted review findings.

### Step 1: Run the full deterministic gate

```bash
.venv/bin/python -m ruff check src tests
.venv/bin/python -m pytest -v
.venv/bin/python -m pytest mcp-server/tests -v
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
.venv/bin/python /Users/wangpeng/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
.venv/bin/python /Users/wangpeng/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/nature-academic-search
claude plugin validate --strict plugins/nature-academic-search
git diff --check
git status --short
```

Expected: zero lint/test/validator/build failures and only intentional artifacts.

### Step 2: Run explicit live smoke checks

Use the scheduled smoke command or source-specific preflight with bounded queries.
Do not run paid/deep pagination. Record:

- timestamp;
- source attempted;
- HTTP success/failure category;
- returned schema parse success;
- skipped credentialed checks;
- no exact result-count expectation.

Do not commit raw third-party result payloads or credentials.

### Step 3: Request code review

Use @requesting-code-review to inspect:

- backward-compatible MCP signatures;
- secret handling and error redaction;
- source/entity routing;
- deduplication and metric provenance;
- bounded requests and retries;
- ClinicalTrials.gov scientific semantics;
- Skill claims matching actual adapters.

### Step 4: Address accepted findings with TDD

For every accepted defect:

1. add a failing focused test;
2. verify the failure is for the intended reason;
3. implement the smallest fix;
4. rerun focused and full gates;
5. commit review fixes separately.

### Step 5: Verify clean feature state

Run the full deterministic gate again after all review fixes. Record exact test
counts and current commit SHA.

### Step 6: Stop before release

Report:

- implemented source roles;
- exact local verification results;
- live smoke limitations;
- compatibility changes;
- recommended semantic version (`0.2.0` unless scope changes);
- branch/worktree location.

Do not merge, tag, publish, or create a GitHub release until the user selects the
integration and release path.

## Execution Checkpoints

Use these checkpoints when executing the plan:

1. **After Task 5:** OpenAlex and Europe PMC work as default publication sources;
   existing three-source calls remain green.
2. **After Task 6:** Semantic Scholar explicit search/enrichment is bounded and
   source-attributed.
3. **After Task 8:** ClinicalTrials.gov and new identifiers work through the
   unchanged four MCP tools.
4. **After Task 10:** Skill, package, plugin, and docs make no unsupported source
   claims.
5. **After Task 11:** full review evidence is ready for an explicit merge/release
   decision.
