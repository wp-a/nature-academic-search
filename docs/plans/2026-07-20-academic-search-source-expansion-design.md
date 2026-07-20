# Academic Paper Search Source Expansion Design

**Date:** 2026-07-20
**Status:** Approved for planning
**Scope:** OpenAlex, Semantic Scholar, Europe PMC, and ClinicalTrials.gov

## Summary

Expand Academic Paper Search from three publication sources to a layered source
system without weakening provenance, partial-failure behavior, or the four
existing MCP tool contracts.

The approved architecture is:

- Add OpenAlex and Europe PMC to the default publication search set.
- Add Semantic Scholar as an explicit publication source and citation-graph
  enrichment provider, not as an unconditional default request.
- Add ClinicalTrials.gov as a separate `trial` entity source routed through the
  existing `search_papers` and `get_paper_by_id` tools.
- Preserve existing PubMed, CrossRef, and arXiv behavior and identifiers.
- Keep publication and trial records structurally distinct and never deduplicate
  one entity type into the other.

This is a backward-compatible feature design. A later implementation may target
`0.2.0`, but version preparation, publishing, and repository release are separate
decisions and are not authorized by this design task.

## Why This Shape

The four sources have different jobs:

| Source | Role | Entity | Default publication search |
|---|---|---|---|
| OpenAlex | Broad cross-disciplinary recall and identifier linking | `publication` | Yes |
| Semantic Scholar | Citation graph, references, related-paper discovery | `publication` | No |
| Europe PMC | Biomedical coverage, PMCID, preprints, open-full-text metadata | `publication` | Yes |
| ClinicalTrials.gov | Trial registration, status, interventions, enrollment | `trial` | Not applicable |

Treating all four as interchangeable paper databases would create three defects:

1. Semantic Scholar's lower request budget would slow or destabilize every
   ordinary search.
2. Europe PMC and PubMed overlap heavily, so naive aggregation would inflate
   counts and duplicate records.
3. ClinicalTrials.gov records are registrations, not publications; presenting
   them as papers would be scientifically misleading.

## Official API Basis

The design was checked against current official documentation on 2026-07-20:

- OpenAlex authentication and costs:
  <https://developers.openalex.org/api-reference/authentication>
- OpenAlex works endpoint:
  <https://developers.openalex.org/api-reference/works/list-works>
- Semantic Scholar Academic Graph API:
  <https://api.semanticscholar.org/api-docs/graphs>
- Europe PMC REST service:
  <https://dev.europepmc.org/RestfulWebService>
- ClinicalTrials.gov API v2:
  <https://clinicaltrials.gov/data-about-studies/learn-about-api>

The local `chub` documentation helper was unavailable, so official primary
documentation is the source of record for this design. API response fixtures
must be refreshed against these official schemas before implementation.

Important operational constraints:

- OpenAlex supports anonymous daily usage and a larger free daily budget with
  an API key. Search requests consume more budget than singleton lookups. The
  adapter must expose rate-limit/cost metadata when returned and must not deep
  paginate automatically.
- Semantic Scholar should use `x-api-key` when configured and apply conservative
  throttling. Anonymous shared capacity is not reliable enough for default
  fan-out.
- Europe PMC overlaps with PubMed but adds PMCID, open-full-text metadata,
  preprints, and additional biomedical records.
- ClinicalTrials.gov API v2 exposes trial records and data version timestamps.
  These records require NCT-specific fields and status dates.

## Goals

- Improve cross-disciplinary and biomedical recall.
- Preserve exact source provenance after deduplication.
- Add source-specific identifiers without breaking current result consumers.
- Support clinical-trial discovery without calling trials papers.
- Preserve partial success when any one source fails, times out, or is
  rate-limited.
- Keep all API credentials optional, environment-driven, and absent from logs.
- Keep the MCP surface at exactly four stable tool names.

## Non-Goals

- Google Scholar, Scopus, Web of Science, Embase, CNKI, or Wanfang access.
- Automated paywalled full-text retrieval.
- Unlimited pagination, bulk corpus mirroring, or citation-network crawling.
- Trial risk-of-bias assessment or publication-to-trial matching by model guess.
- A full systematic-review screening workflow.
- Automatic release, PyPI publishing, or migration of the technical package
  name.

## Compatibility Contract

The following MCP tool names remain unchanged:

- `search_papers`
- `get_paper_by_id`
- `get_citation`
- `lookup_mesh`

Existing calls must continue to work:

```json
{"query": "prime editing"}
```

```json
{"query": "prime editing", "sources": ["pubmed", "crossref", "arxiv"]}
```

```json
{"id": "10.1000/example", "id_type": "auto"}
```

New optional parameters extend rather than replace the current interface:

```python
search_papers(
    query: str,
    sources: list[str] | None = None,
    rows: int = 5,
    type: str | None = None,
    entity_type: str = "publication",
    enrich: list[str] | None = None,
) -> str
```

Rules:

- `entity_type="publication"` accepts publication sources only.
- `entity_type="trial"` defaults to `clinicaltrials_gov` and rejects publication
  sources.
- Mixed publication/trial result lists are rejected rather than silently
  combined.
- `enrich=["semantic_scholar"]` enriches the already deduplicated top results;
  it does not increase the raw search count.
- `sources=["semantic_scholar"]` remains available when the user explicitly
  wants Semantic Scholar's own relevance search.

`get_paper_by_id` keeps its name for compatibility but may return either a
`publication` or `trial` record. `get_citation` rejects `nct` identifiers with a
structured message because a trial registration is not a paper citation.

## Source Names and Defaults

Canonical source names are stable snake-case identifiers:

```python
DEFAULT_PUBLICATION_SOURCES = (
    "crossref",
    "pubmed",
    "arxiv",
    "openalex",
    "europe_pmc",
)

OPTIONAL_PUBLICATION_SOURCES = ("semantic_scholar",)
TRIAL_SOURCES = ("clinicaltrials_gov",)
```

The response must distinguish:

- `sources_queried`: sources for which a request was attempted;
- `sources_succeeded`: sources returning a valid response, including zero hits;
- `sources_skipped`: configured enrichers or optional sources not called, with a
  reason;
- `errors`: attempted sources that failed.

An absent optional API key is not a reason to fabricate success. OpenAlex may use
its documented anonymous allowance; Semantic Scholar enrichment without a key
must either use conservative anonymous access or be reported as skipped after a
preflight/rate-limit failure.

## Entity Model

### Publication

Existing fields remain available. New normalized fields are additive:

```json
{
  "entity_type": "publication",
  "title": "...",
  "authors": ["..."],
  "year": 2026,
  "publication_date": "2026-03-01",
  "journal": "...",
  "abstract": "...",
  "doi": "10.xxxx/example",
  "pmid": "12345678",
  "pmcid": "PMC1234567",
  "arxiv_id": "2401.12345",
  "openalex_id": "W2741809807",
  "semantic_scholar_id": "...",
  "source": "openalex",
  "source_id": "W2741809807",
  "source_url": "https://openalex.org/W2741809807",
  "sources": ["openalex", "crossref"],
  "source_records": [
    {"source": "openalex", "source_id": "W2741809807", "source_url": "..."}
  ],
  "citation_count": 42,
  "citation_count_source": "openalex",
  "citation_counts": {"openalex": 42, "semantic_scholar": 39},
  "is_open_access": true,
  "fulltext_url": "...",
  "retrieved_at": "2026-07-20T00:00:00Z"
}
```

`citation_count` remains for compatibility, but every populated value must carry
`citation_count_source`; all observed source-specific values are retained in
`citation_counts`. No source-specific count is described as absolute.

### Trial

ClinicalTrials.gov records use a separate shape:

```json
{
  "entity_type": "trial",
  "title": "...",
  "nct_id": "NCT01234567",
  "source": "clinicaltrials_gov",
  "source_id": "NCT01234567",
  "source_url": "https://clinicaltrials.gov/study/NCT01234567",
  "study_type": "INTERVENTIONAL",
  "overall_status": "RECRUITING",
  "conditions": ["..."],
  "interventions": [{"type": "DRUG", "name": "..."}],
  "sponsor": "...",
  "enrollment": 120,
  "locations": [{"facility": "...", "country": "..."}],
  "start_date": "2026-01",
  "completion_date": "2028-06",
  "last_update_posted": "2026-07-01",
  "registry_data_timestamp": "...",
  "linked_publications": [],
  "retrieved_at": "2026-07-20T00:00:00Z"
}
```

Missing trial fields remain absent or `null`; the adapter must not infer status,
phase, intervention, or results from prose.

## Identifier Routing

Add identifier types without changing existing detection:

| Type | Detection | Source |
|---|---|---|
| `doi` | Existing DOI rules | CrossRef, with optional enrichment |
| `pmid` | Existing PMID rules | PubMed |
| `arxiv` | Existing arXiv rules | arXiv |
| `pmcid` | `PMC` followed by digits | Europe PMC |
| `openalex` | `W` followed by digits or OpenAlex work URL | OpenAlex |
| `nct` | `NCT` followed by 8 digits | ClinicalTrials.gov |
| `semantic_scholar` | Explicit type for S2 paper ID | Semantic Scholar |

Semantic Scholar paper IDs are not auto-detected when ambiguous. Callers must
use `id_type="semantic_scholar"` unless the input is an unambiguous Semantic
Scholar paper URL.

## Adapter Interface

Each source adapter implements only its actual capabilities:

```python
class PublicationSource(Protocol):
    name: str

    def search(
        self,
        query: str,
        rows: int = 5,
        *,
        filter_type: str | None = None,
    ) -> dict[str, Any]: ...
```

Optional methods are capability-registered rather than assumed:

- `get_by_id(identifier)`
- `enrich(record)`
- `get_citations(identifier, rows)`
- `get_references(identifier, rows)`

A source registry maps source name to adapter and capabilities. The coordinator
must not special-case every source with a growing `if source == ...` chain.

## Request Layer

Four new JSON APIs should share a small internal request helper rather than
duplicate retry and redaction logic. It is not a mandate to rewrite the three
existing adapters in the same release.

The helper must:

- use explicit connect/read timeouts;
- accept query parameters and headers separately;
- retry `429`, `502`, `503`, and `504` at most twice;
- honor `Retry-After` when it is a bounded numeric value;
- otherwise use bounded exponential backoff;
- raise `DataSourceError` with the source name and HTTP status;
- never include API keys or full authorization headers in logs/errors;
- return both decoded JSON and selected response metadata;
- expose OpenAlex rate-limit/cost headers without exposing credentials.

## Query Translation

The MCP input remains a user-level query, not a promise that every source uses
identical syntax.

- OpenAlex: pass natural-language terms through `search`; map supported work
  types through `filter`.
- Europe PMC: use its query parameter and escape only transport syntax; do not
  claim PubMed field tags were honored unless explicitly translated.
- Semantic Scholar: use paper relevance search for explicit searches and ID
  lookups for enrichment.
- ClinicalTrials.gov: use API v2 study query parameters and return trial filters
  only when they are explicitly represented by the tool contract.

Unsupported source-specific syntax is reported in response metadata rather than
silently rewritten. This release does not introduce a general query language.

## Deduplication and Merge Rules

Publication keys, in priority order:

1. normalized DOI;
2. PMID;
3. PMCID;
4. normalized arXiv ID;
5. OpenAlex ID;
6. Semantic Scholar paper ID;
7. normalized title plus year.

Trial keys:

1. normalized NCT ID only.

Every key is namespaced by `entity_type`, so a trial and a publication cannot
merge even when their titles match.

Merge behavior:

- preserve first-source ordering for backward compatibility;
- append unique `sources` in observed order;
- retain every `source_record`;
- fill missing scalar metadata but do not overwrite a non-empty field merely
  because another source differs;
- retain conflicting identifiers or metadata in a structured `conflicts` list;
- retain all citation counts by source and expose which source supplied the
  compatibility `citation_count` value;
- never use title-only matching without year for publications;
- never title-match trials.

## Semantic Scholar Enrichment

Enrichment runs after publication deduplication and is bounded to the returned
top `rows` records.

Lookup priority:

1. DOI;
2. arXiv ID;
3. PMID when supported;
4. Semantic Scholar paper ID already present.

Do not keyword-search each record as a fallback. A missing identifier produces a
`sources_skipped` entry for that record rather than a speculative match.

Enrichment may add:

- Semantic Scholar paper ID;
- source-attributed citation/reference counts;
- references/citations only when the caller explicitly requests them in a
  later bounded extension;
- open-access/PDF URLs labelled as Semantic Scholar metadata.

The initial implementation should not recursively traverse citation graphs.

## Configuration

Add optional configuration properties and matching environment variables:

| Source | Environment variables |
|---|---|
| OpenAlex | `OPENALEX_API_KEY`, `OPENALEX_TIMEOUT` |
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY`, `SEMANTIC_SCHOLAR_TIMEOUT` |
| Europe PMC | `EUROPE_PMC_TIMEOUT` |
| ClinicalTrials.gov | `CLINICALTRIALS_GOV_TIMEOUT` |

TOML sections use the canonical source names. API keys are read at request time,
are never written by the installer, and are never emitted by preflight.

## Failure and Cost Behavior

The coordinator preserves successful source results when another source fails.

Each error entry contains:

```json
{
  "source": "openalex",
  "kind": "rate_limited",
  "status": 429,
  "retryable": true,
  "message": "daily or request rate limit reached"
}
```

Messages must be actionable but secret-free. A user-requested source that was
not attempted is `sources_skipped`, not a success.

OpenAlex response cost and remaining-budget data, when present, are summarized
under `source_meta.openalex`. The coordinator never paginates beyond the
requested `rows` count in this release.

## Skill Routing and User-Facing Contract

The Skill remains Chinese-first and must explain source roles:

- broad paper search: PubMed, CrossRef, arXiv, OpenAlex, Europe PMC;
- citation graph or related papers: explicitly add Semantic Scholar;
- clinical trials: set `entity_type=trial` and use ClinicalTrials.gov;
- do not claim trial registrations are peer-reviewed papers;
- disclose overlapping source coverage and deduplication counts;
- disclose configured, queried, skipped, failed, and successful sources.

The Skill must not claim access to a source merely because its adapter exists.
The actual result response is the evidence that a source was queried.

## Testing Strategy

All deterministic tests use mocked HTTP responses or sanitized fixtures.

Required coverage:

- adapter normalization for every source;
- empty query and malformed response handling;
- timeout, `429`, `5xx`, retry, and secret-redaction behavior;
- identifier detection for PMCID, OpenAlex, NCT, and explicit S2 IDs;
- publication deduplication across DOI/PMID/PMCID/arXiv/OpenAlex/S2;
- trial isolation from publication records;
- source-specific citation-count provenance;
- default versus explicit source routing;
- partial success and `sources_skipped` semantics;
- Semantic Scholar enrichment bounded to top results and strong IDs;
- existing four MCP tool names and old call signatures;
- plugin mirror, package data, README, Skill source boundaries, and installer
  behavior.

Scheduled network smoke tests may make one low-cost query per source. They must
remain outside normal CI, skip credentialed checks when secrets are absent, and
never assert exact result counts.

## Delivery Phases

### Phase 1: Contract and infrastructure

- Add source capability registry and normalized entity fields.
- Add shared request helper for new JSON sources.
- Add fixtures and failure/provenance tests.

### Phase 2: Default publication sources

- Implement OpenAlex.
- Implement Europe PMC.
- Add them to default publication routing.
- Verify cross-source deduplication and partial failure.

### Phase 3: Optional enrichment

- Implement Semantic Scholar explicit search and strong-ID enrichment.
- Add source-attributed metrics and conservative throttling.

### Phase 4: Trial entity

- Implement ClinicalTrials.gov API v2.
- Add `entity_type=trial`, NCT ID routing, and trial-specific result contract.
- Reject mixed entity source lists and trial citation generation.

### Phase 5: Skill, docs, and release readiness

- Update canonical Skill and packaged mirror.
- Update README, source tiers, installation/preflight docs, and maintenance
  guidance.
- Run local unit, compatibility, build, plugin, Skill, and opt-in network gates.
- Prepare a release only after separate user approval.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Default fan-out becomes slow | Concurrent requests, explicit timeouts, bounded rows, partial success |
| OpenAlex budget is consumed unexpectedly | No deep pagination, surface cost metadata, document optional key |
| Semantic Scholar throttles normal searches | Explicit source/enrichment only, conservative rate limit |
| PubMed and Europe PMC duplicate results | DOI/PMID/PMCID priority deduplication |
| Trial registrations appear as papers | Separate entity type and route validation |
| Citation counts conflict | Preserve per-source counts and source attribution |
| API schema drift breaks parsing | Sanitized fixtures, defensive parsing, scheduled smoke tests |
| Credentials leak in errors | Shared redaction helper and regression tests |
| Existing clients break | Preserve four tools, existing parameters, fields, and source names |

## Acceptance Criteria

Implementation is complete only when:

1. Existing three-source calls remain behaviorally compatible.
2. Default publication search attempts OpenAlex and Europe PMC and reports each
   source outcome.
3. Semantic Scholar is explicit and does not add unbounded requests.
4. ClinicalTrials.gov returns `trial` entities and never merges with papers.
5. PMCID, OpenAlex, NCT, and explicit Semantic Scholar IDs resolve correctly.
6. Deduplication preserves source records, conflicts, and citation-count
   provenance.
7. One source can fail without discarding other valid results.
8. No API key appears in logs, errors, fixtures, or committed output.
9. Existing and new unit/compatibility suites, Ruff, package build, plugin
   validators, Skill validator, and documentation checks pass.
10. No version tag, GitHub release, or PyPI publication occurs without separate
    approval.
