# Citation Files

Use the installed package for deterministic batch export:

```bash
nature-academic-search citation --input refs.txt --format ris --output references/
```

Input lines may use:

```text
PMID:28344011
DOI:10.1038/nature14539
ARXIV:1706.03762
QUERY:prime editing AND review[Publication Type]
AUTHOR:Dheda TITLE:drug-resistant tuberculosis
```

Supported outputs:

| Format | Extension | Use |
|---|---|---|
| NBIB/MEDLINE | `.nbib` | Native PubMed import |
| RIS | `.ris` | EndNote, Zotero, Mendeley |
| BibTeX | `.bib` | LaTeX and reference managers |
| EndNote tagged | `.enw` | EndNote import |

CrossRef and arXiv do not provide NBIB. The CLI falls back to RIS for those
sources. Run `nature-academic-search preflight` before a large network batch.

The `citation` CLI downloads and formats metadata; it does not compare the original
citation against `expected` fields. Verify intended references first with
`get_paper_by_id(expected=...)` or CLI `verify`, then pass their identifiers here.
Unprefixed input lines are PubMed text queries, not direct identifier lookups.

Workflow `0.3.1` performs identifier-based verification automatically. RIS export
defaults to `verified` publications. When the workflow includes `screen`, export
also requires an explicit `include` decision; excluded, pending, missing, invalid,
or failed screening results remain in audit files. Use
`steps: [plan, search, verify, export]` for verification-only export without a model.
Trial registrations remain in JSON and are not exported as journal articles.
Workflow `verification.fields` records checked fields; secondary IDs absent from
the lookup source are listed in `unchecked_identifiers`. RIS includes DOI/PMID only
when that identifier matched the lookup response. Original records remain intact.
Check `exported_count` in `run.json` and keep unresolved or mismatched entries in
the verification report instead of writing plausible-looking citation data.
