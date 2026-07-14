---
name: nature-academic-search
description: Use when searching, verifying, deduplicating, or exporting academic literature across PubMed, CrossRef, and arXiv; building MeSH queries; resolving DOI, PMID, or arXiv identifiers; or producing RIS, BibTeX, NBIB, and ENW citation files.
---

# Nature Academic Search

Coordinate reproducible literature searches with the bundled MCP server. Treat
search results as evidence to verify, not citations to invent.

## Available tools

Use the tool whose name ends with the listed suffix; clients may prepend an MCP
namespace.

| Tool suffix | Purpose |
|---|---|
| `search_papers` | Search PubMed, CrossRef, arXiv, or a selected subset |
| `get_paper_by_id` | Resolve a DOI, PMID, or arXiv identifier |
| `get_citation` | Format one verified record in a named citation style |
| `lookup_mesh` | Find PubMed MeSH descriptors for query construction |

If these tools are unavailable, state that limitation. Do not claim a database
was searched unless a tool or official API actually returned results.

## Core workflow

1. Define the topic, date range, document types, result count, and whether
   preprints are acceptable. Ask only when an omitted choice materially changes
   the result.
2. Select sources: PubMed for biomedical indexing and MeSH, CrossRef for
   publisher metadata and DOI resolution, and arXiv for relevant preprints.
3. Call `search_papers`. Inspect `errors`, `raw_result_count`, `result_count`, and
   `sources` before presenting results.
4. Resolve important or suspicious identifiers with `get_paper_by_id`. Compare
   title, authors, venue, year, and identifier; flag conflicts instead of guessing.
5. Separate peer-reviewed publications from preprints. Report the query, sources,
   cutoff date, and source failures with the result set.
6. Use `get_citation` for individual citations. For batch citation files, use the
   package CLI described in [citation files](references/citation-files.md).

For query construction, source selection, ranking, and verification details, read
[search workflows](references/search-workflows.md).

## Evidence rules

- Never fabricate metadata, abstracts, citation counts, identifiers, or access
  status.
- Prefer DOI matches; otherwise verify PMID or arXiv ID, then normalized title and
  year.
- Preserve successful results when one source fails and disclose the failure.
- Treat citation counts as source-specific snapshots, not absolute truth.
- Do not describe a preprint as peer reviewed without independent evidence.

## Common mistakes

- Broadening the query silently after no results: show the revised query.
- Returning duplicates from publisher and index records: use merged `sources`.
- Exporting unresolved references: keep them in a separate verification report.
- Using free-text PubMed terms when a stable MeSH descriptor is available: call
  `lookup_mesh` first.
