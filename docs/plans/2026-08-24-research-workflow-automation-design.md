# Evidence-Grade Search and Research Workflow Design

## Goal

Turn Academic Paper Search into a reproducible evidence workflow that can later
add deterministic discovery controls and optional model-assisted research
automation through an OpenAI-compatible gateway, without coupling academic data
sources to that gateway.

## Staged Architecture

Implementation is deliberately staged:

1. **A — Evidence-grade search:** add a search-run manifest, stable record IDs,
   and field-level citation verification while preserving the four existing MCP
   tool names.
2. **B — Smart discovery:** add normalized date, language, author, and document
   type filters, source-specific query translation, deterministic relevance
   scoring, and ranking reasons.
3. **C — Research workflow automation:** compose planning, retrieval,
   verification, screening, and export into a declarative local workflow with
   human approval gates and auditable artifacts.

Each stage must pass its own regression suite before the next stage changes the
public contract.

## A: Evidence-Grade Search

### Search-run manifest

`search_papers` adds a `search_run` object to successful search responses. The
object contains a schema version, UUID run ID, UTC start/end timestamps, the
original query, entity type, requested sources, enrichers, row limit, raw and
unique result counts, and a SHA-256 fingerprint of ordered stable record IDs.
It never contains credentials, headers, or raw configuration values.

### Stable records

Each normalized result adds `record_id`. Strong identifiers use a canonical
namespace such as `publication:doi:<normalized-doi>` or
`trial:nct:<normalized-nct-id>`. Records without a strong identifier use a
deterministic SHA-256 fallback over entity type, normalized title, year, and
first author. The ID is additive and does not replace existing identifiers or
source provenance.

### Field-level verification

The existing `get_paper_by_id` tool gains an optional `expected` object with
title, authors, year, journal, and supported identifiers. When present, the
response adds a `verification` object with one of `verified`, `mismatch`,
`not_found`, or `manual_needed`, plus per-field match status, expected/actual
values where safe, and the method. Calls without `expected` retain the current
response shape. Trial records are verified with trial fields and are never
compared as paper citations.

## B: Smart Discovery

B builds on A's stable IDs and provenance. It introduces a normalized filter
model while retaining source-native query syntax internally:

- publication date range, language, author, and document type;
- explicit query translation for PubMed, CrossRef, OpenAlex, and Europe PMC;
- deterministic relevance scores based on title, abstract, subject terms, and
  exact identifier matches;
- `ranking` metadata that states the score version and reasons for ordering.

No model-generated relevance score is treated as evidence quality, and ranking
must remain reproducible from the run manifest.

## C: Research Workflow Automation

The workflow runner is local and declarative. A workflow contains a research
question, ordered steps, source options, verification policy, screening rules,
and output artifacts:

```yaml
workflow: literature-review
question: "生成式 AI 在医学教育中的应用与风险"
steps: [plan, search, verify, screen, export]
search:
  entity_type: publication
  sources: [crossref, pubmed, arxiv, openalex, europe_pmc]
  rows: 20
outputs: [run.json, results.json, verification.json, screening.csv, references.ris, report.md]
```

The planner must pause for user approval before broad retrieval. Screening
outputs include inclusion/exclusion decisions, reasons, evidence fields, and a
human-review state. Export excludes `mismatch` and `manual_needed` records from
the verified citation set unless the user explicitly overrides that policy.

## Gateway Integration

The WPIRONMAN gateway is an optional model provider, not a scholarly source.
The runner uses an OpenAI-compatible HTTP adapter configured only through
environment variables:

```bash
ACADEMIC_SEARCH_LLM_PROVIDER=openai_compatible
ACADEMIC_SEARCH_LLM_BASE_URL=https://api.wpironman.top/v1
ACADEMIC_SEARCH_LLM_API_KEY=<secret>
ACADEMIC_SEARCH_LLM_MODEL=<model-name>
ACADEMIC_SEARCH_LLM_PROTOCOL=responses_http
```

The adapter probes `/v1/models`, uses ordinary HTTP rather than Responses
WebSocket, validates structured JSON, and retries malformed model output at
most once. Gateway failures mark only model-assisted steps as skipped; direct
source search, verification, and export remain usable. The API key never enters
the run manifest, logs, prompts saved as artifacts, or repository files.

By default, only titles, abstracts, identifiers, and user-approved metadata may
be sent to the provider. Full text requires an explicit workflow setting and a
separate privacy warning.

## Compatibility

- Keep the existing four MCP tool names and existing calls valid.
- Add optional parameters and additive response fields only.
- Keep publication, preprint, and trial entity boundaries explicit.
- Keep source provenance and partial-failure reporting unchanged.
- Do not require the gateway for the base package or for A/B deterministic
  search capabilities.

## Verification Strategy

Each stage uses test-first implementation. A covers manifest schema, UTC
timestamps, stable IDs, field comparisons, mismatch/manual-needed states, trial
boundaries, secret redaction, and old-call compatibility. B adds filter routing,
ranking determinism, score-version changes, and source-specific query fixtures.
C adds workflow validation, approval gates, artifact manifests, provider
fallbacks, malformed JSON retries, and gateway-unavailable behavior.
