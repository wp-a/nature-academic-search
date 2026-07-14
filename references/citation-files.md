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

Export only verified records. Keep unresolved or mismatched entries in a separate
report instead of writing plausible-looking citation data.
