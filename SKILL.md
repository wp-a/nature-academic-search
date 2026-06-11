---
name: nature-academic-search
description: >-
  Multi-source literature search, citation verification, MeSH search strategy,
  citation file management (.nbib/.ris/.bib conversion), and reference management
  (BibTeX, related articles, ID conversion) via MCP tools (PubMed, CrossRef, arXiv).
  Use when the user needs coordinated multi-step literature workflows beyond a
  single MCP call.
---

# Academic Search

Multi-source literature search, citation verification, citation format conversion,
and reference management via MCP tools.

## MCP Tools

### Core Search

| Tool | Source | Best For |
|------|--------|----------|
| `pubmed_search_articles` | PubMed MCP | Biomedical, MeSH, clinical trials |
| `search_crossref` | paper-search MCP | Cross-disciplinary, citation counts |
| `search_arxiv` | paper-search MCP | Preprints (physics, math, CS, biology) |

### Extended Search

| Tool | Source | Best For |
|------|--------|----------|
| `search_google_scholar` | paper-search MCP | Broad academic search (scraped) |
| `search_semantic_scholar` | paper-search MCP | Citation graph, field-of-study filters |
| `search_biorxiv` | paper-search MCP | Biology preprints |
| `search_medrxiv` | paper-search MCP | Medical preprints |
| `search_webofscience` | paper-search MCP | Curated index, citation reports |
| `search_scopus` | paper-search MCP | Broad scholarly database |

### PubMed Utilities

| Tool | Purpose |
|------|---------|
| `pubmed_fetch_articles` | Full metadata by PMID |
| `pubmed_find_related` | Related article discovery |
| `pubmed_format_citations` | APA / MLA / BibTeX / RIS formatting |
| `pubmed_convert_ids` | DOI ↔ PMID ↔ PMCID conversion |
| `pubmed_lookup_mesh` | MeSH term exploration and hierarchy |
| `pubmed_lookup_citation` | Bibliographic citation → PMID lookup |

## Source Routing

See [Source Tiers & Reliability](references/source-tiers.md) for the complete reliability classification and fallback routing rules. The T1→T2→T3 fallback chain is the standard execution order across all workflows.

Quick guide:

| User need | Primary (T1) | Secondary (T2) | Last Resort (T3) |
|-----------|-------------|-----------------|-------------------|
| Medical / clinical | PubMed | Semantic Scholar | Google Scholar |
| Cross-disciplinary | CrossRef | Semantic Scholar | Scopus |
| Preprints / CS / physics | arXiv | bioRxiv / medRxiv | — |
| Exhaustive review | PubMed + CrossRef + arXiv | Semantic Scholar + bioRxiv/medRxiv | WoS / Scopus |
| Citation count sensitive | Semantic Scholar | CrossRef | — |
| Chinese literature | — | — | CNKI / 万方 (manual) |

## Workflows

| # | Workflow | Reference |
|---|----------|-----------|
| 1 | Multi-Source Literature Search | [wf1](references/workflows/wf1-multi-source-search.md) |
| 2 | Citation Verification | [wf2](references/workflows/wf2-citation-verification.md) |
| 3 | MeSH Search Strategy | [wf3](references/workflows/wf3-mesh-strategy.md) |
| 4 | Citation File Management | [wf4](references/workflows/wf4-citation-file-mgmt.md) |
| 5 | Reference Management | [wf5](references/workflows/wf5-reference-mgmt.md) |

## Shared Modules

| Module | Purpose |
|--------|---------|
| [Dedup Engine](references/dedup-engine.md) | Unified deduplication (WFs 1, 2, 5a) |
| [Citation Parser](references/citation-parser.md) | Extract citations from documents (WF 2) |
| [Search Strategy](references/search-strategy.md) | Query construction, source selection, ranking |
| [RIS/BibTeX Format](references/ris-bibtex-format.md) | Format specifications and field mappings |
| [Format Converter](scripts/format-converter.py) | Multi-source .nbib/.ris/.bib downloader |

## Environment Setup

### API Keys (optional but recommended)

| Service | Env Var | Register At | Free Tier |
|---------|---------|-------------|-----------|
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | [api.semanticscholar.org](https://api.semanticscholar.org/) | 100 req/s with key (1/s without) |
| NCBI E-utilities | `NCBI_API_KEY` | [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/) | 10 req/s with key (3/s without) |

Set via `export` or `.env` file.

### Proxy (if behind firewall)

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

### Pre-flight Check

```bash
python scripts/preflight.py
```

Run before batch operations to verify API endpoints are reachable.

### Format Converter Dependencies

The format converter (`scripts/format-converter.py`) uses Python stdlib only — no extra dependencies. Run `python scripts/format-converter.py --test` to verify the conversion pipeline.

## Error Handling

- **MCP tool unavailable**: report specific failure, continue with remaining tools.
- **No results**: broaden terms, try alternative sources, suggest user refine query.
- **Script failure (2x)**: fall back to manual generation from MCP-fetched metadata.

## Limitations

- Google Scholar and Semantic Scholar are scraped (not API-backed) — results may vary.
- Chinese literature (CNKI / 万方) not indexed by CrossRef or PubMed.
- Citation counts may be delayed (CrossRef updates monthly).
