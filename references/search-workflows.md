# Search Workflows

## Source routing

| Need | Sources | Notes |
|---|---|---|
| Biomedical or clinical literature | PubMed + CrossRef | Build MeSH terms first when recall matters |
| DOI or publisher metadata | CrossRef | Verify returned DOI against title and year |
| Computer science, physics, or preprints | arXiv + CrossRef | Label preprints explicitly |
| Broad mixed-domain review | PubMed + CrossRef + arXiv | Expect partial overlap and deduplication |

Do not imply that Google Scholar, Semantic Scholar, Scopus, Web of Science, CNKI,
or other sources were searched unless a separate available tool actually queried
them.

## Query construction

1. Split the question into concepts: population/system, intervention/exposure,
   comparator, outcome, method, and exclusions as applicable.
2. Create one synonym group per concept.
3. For PubMed, call `lookup_mesh` for stable biomedical concepts. Combine MeSH
   descriptors with title/abstract synonyms.
4. Keep a human-readable query record. Database syntax is not interchangeable;
   adapt field tags rather than passing a PubMed query verbatim to every source.
5. Add date, article-type, and language filters only when the user requested them
   or the scope requires them.

## Multi-source search

Call `search_papers` with explicit `sources` when scope is known. Start with a
small result count while refining the query, then increase it for the final pass.

Inspect:

- `errors`: source failures that must be disclosed;
- `raw_result_count`: records before deduplication;
- `result_count`: unique records returned;
- `sources`: provenance merged into each record.

If a source fails, keep successful records and retry only the failed source. Avoid
repeating successful requests unnecessarily.

## Verification

For records used in a manuscript, recommendation, or export:

1. Resolve DOI, PMID, or arXiv ID with `get_paper_by_id`.
2. Compare title, first author, venue, year, and identifier.
3. Classify the record as `verified`, `mismatch`, `not_found`, or `manual_needed`.
4. Explain mismatches field by field. Never repair metadata by intuition.
5. Prefer the publisher record when it matches a preprint, while preserving the
   preprint identifier and relationship.

## Result reporting

Return the query, databases, search date, date cutoff, inclusion rules, source
failures, and unique results. Include identifiers and provenance. Separate
peer-reviewed papers, preprints, and unresolved records.
